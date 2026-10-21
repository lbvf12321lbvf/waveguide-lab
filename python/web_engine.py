"""Browser adapter. All dimensions enter in nm / µm / cm, core uses SI.

This module runs unchanged in CPython and Pyodide. No network, arbitrary code,
pickle loading, Tk, CUDA, or subprocesses. JSON is the public boundary.
"""
from __future__ import annotations
import io
import base64
import json
import math
import struct
import time
from dataclasses import replace

import numpy as np
from PIL import Image
from scipy.special import jn_zeros, jv
from image_color import decode_intensity, color_config

from waveguide_core.config import WaveguideConfig
from waveguide_core.cylindrical_modes import Mode, solve_mode, bessel_seed, _marcatili_amplitude_guess
from waveguide_core.projection import (
    make_grid, gaussian_beam_field, build_profiles, decompose_field, field_power,
    _profile_components, Field2D,
)
from waveguide_core.angular_analysis import (
    beam_from_angle_offset, angular_candidate_mode_specs,
    estimate_excitation_polar_quadrature, mode_angle_deg,
)
from waveguide_core.experiment import (
    preprocess_experimental_image, automatic_roi, refine_roi_from_circular_edge,
    _sample_camera_on_grid, polar_diagnostics, _rank_single_mode_similarity,
    _coherent_fit,
)

VERSION = '1.0.0'
AUTO_RESIDUAL_TARGET = 0.001
WORKING_MEMORY_MB = 650
MAX_CANDIDATES = 6000
DEFAULTS = dict(wavelength_nm=800, diameter_um=300, waist_um=45,
                theta_deg=0, azimuth_deg=0, offset_um=0, offset_azimuth_deg=0,
                polarization='x', epsilon_real=-31.021, epsilon_imag=0.40948,
                mode_selection='auto', max_modes=32, samples=96, length_cm=40, families='all')
_simulation = None
_image = None
_image_meta = None
_source_image = None
_color_config = None
_palette_distance = None


def clean(value):
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    if isinstance(value, np.ndarray):
        return clean(value.tolist())
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        return float(value) if math.isfinite(float(value)) else None
    return value


def number(data, key, low, high, default=None, integer=False):
    try:
        raw = data.get(key, default)
        if isinstance(raw, bool):
            raise ValueError()
        value = float(raw)
    except (TypeError, ValueError):
        raise ValueError(f'Parameter {key} must be a number.') from None
    if not math.isfinite(value) or not low <= value <= high or (integer and value != int(value)):
        raise ValueError(f'Parameter {key} must be between {low} and {high}.')
    return int(value) if integer else value


def validate(data):
    d = dict(DEFAULTS)
    d.update({k: v for k, v in data.items() if k in DEFAULTS})
    # Older saved calculations specified a manual limit without a selection mode.
    if 'mode_selection' not in data and 'max_modes' in data:
        d['mode_selection'] = 'manual'
    bounds = {'wavelength_nm': (350, 2000), 'diameter_um': (10, 1000),
              'waist_um': (1, 1000), 'theta_deg': (0, 30), 'azimuth_deg': (-180, 180),
              'offset_um': (0, 500), 'offset_azimuth_deg': (-180, 180),
              'epsilon_real': (-1000, -0.1), 'epsilon_imag': (0.00001, 1000),
              'max_modes': (1, MAX_CANDIDATES), 'samples': (48, 256), 'length_cm': (0.01, 200)}
    for k, limits in bounds.items():
        d[k] = number(d, k, *limits, integer=k in ('max_modes', 'samples'))
    if d['polarization'] not in ('x', 'y', 'circular') or d['families'] not in ('all', 'he'):
        raise ValueError('Unknown polarization or mode family.')
    if d['mode_selection'] not in ('auto', 'manual'):
        raise ValueError('Unknown mode selection method.')
    if d['offset_um'] >= d['diameter_um'] / 2:
        raise ValueError('The beam centre must be inside the waveguide.')
    if d['waist_um'] < 4 * d['diameter_um'] / (d['samples'] - 1):
        raise ValueError('The beam is too narrow for this grid. Increase resolution or beam waist.')
    phase_samples = 4 * d['diameter_um'] * 1000 / d['wavelength_nm'] * math.sin(math.radians(d['theta_deg'])) + 1
    if d['samples'] < phase_samples:
        raise ValueError(f'This launch angle requires at least {math.ceil(phase_samples)} samples across the diameter. '
                         'Increase the grid or reduce angle / diameter. The web limit is 256.')
    return d


def modal_memory_mb(samples, profile_count):
    """Conservative estimate: both field components, LAPACK copies and Gram matrix."""
    return (samples**2 * 2 * profile_count * 16 * 5 + 32 * profile_count**2) / 2**20 + 32


def mode_pool(eligible, roots, d):
    """Keep ranking order; automatic mode may stop at resource bounds explicitly."""
    automatic = d['mode_selection'] == 'auto'
    candidates = eligible if automatic else eligible[:d['max_modes']]
    resolved = [s for s in candidates if math.ceil(4 * roots[s.name] / math.pi + 1) <= d['samples']]
    if not automatic and len(resolved) != len(candidates):
        needed = max(math.ceil(4 * roots[s.name] / math.pi + 1) for s in candidates)
        raise ValueError(f'The requested modes need at least {needed} grid samples. '
                         'Increase resolution or reduce the manual mode limit.')
    pool, profiles = [], 0
    for spec in resolved:
        next_profiles = profiles + (1 if spec.family in ('TE', 'TM') else 2)
        if modal_memory_mb(d['samples'], next_profiles) > WORKING_MEMORY_MB:
            if not automatic:
                raise ValueError(f'The requested basis exceeds the {WORKING_MEMORY_MB} MiB working-memory budget. '
                                 f'At this grid, the first {len(pool)} modes fit. Reduce the manual mode limit.')
            break
        pool.append(spec)
        profiles = next_profiles
    if not pool:
        raise ValueError('No excited modes can be resolved on this grid. Increase grid resolution.')
    reason = ('memory_limit' if len(pool) < len(resolved) else
              'grid_limit' if len(resolved) < len(candidates) else 'candidate_limit')
    return pool, reason, len(candidates) - len(resolved)


def physics(d):
    cfg = WaveguideConfig(wavelength=d['wavelength_nm'] * 1e-9,
                         diameter=d['diameter_um'] * 1e-6,
                         metal_epsilon=complex(d['epsilon_real'], d['epsilon_imag']))
    px, py = {'x': (1, 0), 'y': (0, 1), 'circular': (2**-0.5, 1j * 2**-0.5)}[d['polarization']]
    beam = beam_from_angle_offset(cfg, theta_deg=d['theta_deg'],
                                 tilt_azimuth_deg=d['azimuth_deg'], offset_um=d['offset_um'],
                                 offset_azimuth_deg=d['offset_azimuth_deg'], waist=d['waist_um'] * 1e-6,
                                 polarization_x=px, polarization_y=py)
    return cfg, beam


def field_payload(field, grid, reference=None):
    intensity = np.abs(field.Ex)**2 + np.abs(field.Ey)**2
    peak = float(np.max(intensity))
    component = field.Ex if np.max(np.abs(field.Ex)) >= np.max(np.abs(field.Ey)) else field.Ey
    phase = np.angle(component)
    valid_phase = grid.core_mask & (np.abs(component)**2 > max(float(np.max(np.abs(component)**2)) * 1e-8, 1e-300))
    intensity = np.where(grid.core_mask, intensity / max(reference or peak, 1e-300), np.nan)
    phase = np.where(valid_phase, phase, np.nan)
    # Full grid retained for numerical export, no resampling hides undersampling.
    return {'size': len(grid.x), 'intensity': np.round(intensity, 7).ravel(),
            'phase': np.round(phase, 6).ravel(), 'peak': peak,
            'phase_component': 'Ex' if component is field.Ex else 'Ey'}


def simulate(data, progress=lambda *_: None):
    global _simulation
    started = time.perf_counter()
    d = validate(data)
    cfg, beam = physics(d)
    progress(0.03, 'Selecting the modal basis')
    specs, _, roots, window = angular_candidate_mode_specs(
        cfg, beam, min_power_fraction=1e-6, include_eh=d['families'] == 'all',
        include_te_tm=d['families'] == 'all')
    if len(specs) > MAX_CANDIDATES:
        raise ValueError('The catalogue is too large for the browser. Reduce the launch angle or offset.')
    # Resolve both radial oscillations and the maximum angular Fourier order.
    nr = min(512, max(96, int(math.ceil(window.u_max * 1.2))))
    na = min(2048, max(192, 4 * (window.q_max + 1)))
    eligible, rough, _ = estimate_excitation_polar_quadrature(
        cfg, beam, specs, roots, radial_samples=nr, angular_samples=na,
        min_power_fraction=1e-7, max_modes=None, progress_every=None,
        progress_callback=lambda f, _: progress(0.07 + 0.20*f, 'Estimating modal excitation'))
    if not eligible:
        raise ValueError('No excited modes were found in the selected basis.')
    pool, pool_limit, excluded_grid = mode_pool(eligible, roots, d)
    automatic = d['mode_selection'] == 'auto'
    estimates = {r['mode']: r['estimated_power_fraction'] for r in rough}
    cumulative = np.cumsum([estimates[s.name] for s in pool])
    # Overlap weights only seed the basis size; the full least-squares residual
    # controls stopping, since approximate profiles need not be orthogonal.
    count = min(len(pool), max(2, int(np.searchsorted(cumulative, .9 * cumulative[-1])) + 1)) if automatic else len(pool)
    modes, profiles, fallback, passes = [], [], [], []
    original_quality = {}
    grid = make_grid(cfg.radius, d['samples'])
    input_field = gaussian_beam_field(grid, cfg, beam)
    while True:
        for spec in pool[len(modes):count]:
            progress(.28 + .32 * len(modes) / len(pool), f'Solving mode {len(modes)+1} · {spec.name}')
            mode = solve_mode(spec.family, spec.n, spec.m, cfg)
            original_quality[mode.name] = {'converged': mode.converged, 'residual': mode.residual}
            if not mode.converged:
                fallback.append(mode.name)
                beta = math.sqrt(max(0, cfg.k0**2 - (mode.u_seed / cfg.radius)**2))
                alpha = _marcatili_amplitude_guess(mode.family, mode.u_seed, cfg)
                mode = replace(mode, gamma=complex(beta, alpha), converged=True)
            modes.append(mode)
            profiles.extend(build_profiles([mode], grid, cfg))
        progress(.28 + .32 * len(modes) / len(pool), f'Checking input projection · {len(modes)} modes')
        result = decompose_field(input_field, profiles, grid, rcond=1e-9)
        if not np.all(np.isfinite(result.coefficients)):
            raise ValueError('The decomposition is unstable. Change the settings or reduce the mode count.')
        residual_fraction = result.residual_power / result.input_power
        passes.append({'modes': len(modes), 'residual': residual_fraction})
        if not automatic or residual_fraction <= AUTO_RESIDUAL_TARGET or count == len(pool):
            break
        count = min(len(pool), max(count + 4, math.ceil(count * 1.6)))
        del result
    selection = {'method': d['mode_selection'], 'eligible_modes': len(eligible),
                 'available_modes': len(pool), 'excluded_grid_modes': excluded_grid,
                 'requested_limit': None if automatic else d['max_modes'],
                 'target_residual': AUTO_RESIDUAL_TARGET if automatic else None,
                 'target_met': residual_fraction <= AUTO_RESIDUAL_TARGET if automatic else None,
                 'stop_reason': ('target_reached' if residual_fraction <= AUTO_RESIDUAL_TARGET else pool_limit)
                                if automatic else 'manual_limit',
                 'estimated_memory_mb': modal_memory_mb(d['samples'], len(profiles)), 'passes': passes}
    weights = np.abs(result.coefficients)**2
    weight_sum = max(float(np.sum(weights)), 1e-300)
    rows = []
    for coefficient, p, w in zip(result.coefficients, profiles, weights):
        rows.append({'name': p.name, 'mode': p.mode.name, 'family': p.mode.family,
                     'n': p.mode.n, 'm': p.mode.m, 'orientation': p.orientation,
                     'u': p.mode.u_seed, 'coefficient_real': coefficient.real,
                     'coefficient_imag': coefficient.imag, 'weight': float(w / weight_sum),
                     'angle_deg': mode_angle_deg(cfg, p.mode.u_seed),
                     'neff': p.mode.beta / cfg.k0, 'alpha_power_per_m': p.mode.power_attenuation,
                     'fallback': p.mode.name in fallback, **original_quality[p.mode.name]})
    rows.sort(key=lambda r: r['weight'], reverse=True)
    progress(0.80, 'Propagation and output field')
    # Coherent power via the exact discrete Gram matrix, including cross terms.
    mask = grid.core_mask
    matrix = np.column_stack([np.concatenate([p.Ex[mask], p.Ey[mask]]) for p in profiles])
    gram = (matrix.conj().T @ matrix) * grid.area_element
    del matrix
    zs = np.linspace(0, d['length_cm'] / 100, 61)
    gamma = np.array([p.mode.gamma for p in profiles])
    gamma_ref = float(np.max(gamma.real))
    coefficients_z = result.coefficients[None, :] * np.exp(1j * (gamma[None, :] - gamma_ref) * zs[:, None])
    powers = np.real(np.einsum('zi,ij,zj->z', coefficients_z.conj(), gram, coefficients_z)) / result.input_power
    rank = int(np.sum(result.singular_values > result.singular_values[0] * 1e-9))
    warnings = []
    if automatic and not selection['target_met']:
        reason = {'memory_limit': 'working-memory budget', 'grid_limit': 'grid resolution',
                  'candidate_limit': 'available excited modes'}[pool_limit]
        warnings.append(f'Automatic selection stopped at the {reason}: residual {residual_fraction*100:.3f}% '
                        f'exceeds the {AUTO_RESIDUAL_TARGET*100:g}% target. Check grid and basis convergence.')
    if fallback:
        warnings.append(f'{len(fallback)} modes: complex root did not converge; propagation uses a Marcatili estimate. See the table labels.')
    residual_fraction = result.residual_power / result.input_power
    if residual_fraction > .05:
        warnings.append('The basis represents less than 95% of input power. Increase mode count and check grid convergence.')
    if rank < len(profiles):
        warnings.append('The basis is linearly dependent at the selected SVD threshold. Individual coefficients may be unstable.')
    if np.max(powers) > 1+1e-8 or np.any(np.diff(powers) > .005):
        warnings.append('Approximate profiles produce nonmonotonic power or power above 100%. This is not physical gain; check model convergence.')
    _simulation = {'result': result, 'config': d, 'cfg': cfg, 'gamma_ref': gamma_ref}
    payload = {'version': VERSION, 'config': d, 'rows': rows,
               'metrics': {'coupled': result.coupled_power / result.input_power,
                           'residual': residual_fraction, 'transmission': float(powers[-1]),
                           'physical_modes': len(modes), 'profiles': len(profiles), 'rank': rank,
                           'fallback_count': len(fallback), 'candidates': len(specs),
                           'seconds': time.perf_counter()-started},
               'selection': selection, 'warnings': warnings, 'power': {'z_cm': zs * 100, 'fraction': powers},
               'input': field_payload(input_field, grid),
               'field': slice_field({'z_cm': d['length_cm']}),
               'singular_values': result.singular_values}
    progress(1, 'Calculation complete')
    return payload


def slice_field(data):
    if _simulation is None:
        raise ValueError('Run a simulation first.')
    z_cm = number(data, 'z_cm', 0, 200)
    result = _simulation['result']
    # Remove arbitrary rapidly rotating carrier; intensity is unchanged.
    field = result.propagated_field(z_cm / 100)
    phase = np.exp(-1j * _simulation['gamma_ref'] * z_cm / 100)
    field.Ex *= phase
    field.Ey *= phase
    payload = field_payload(field, result.grid)
    payload['z_cm'] = z_cm
    payload['power_fraction'] = field_power(field, result.grid) / result.input_power
    return payload


def read_spe(raw, mode='auto', frame=0):
    if len(raw) < 4100:
        raise ValueError('Invalid SPE: header is shorter than 4100 bytes.')
    version = struct.unpack_from('<f', raw, 1992)[0]
    if not math.isfinite(version) or version >= 3:
        raise ValueError('SPE 2.x is supported. Export SPE 3.x as TIFF.')
    width, height = struct.unpack_from('<H', raw, 42)[0], struct.unpack_from('<H', raw, 656)[0]
    frames = struct.unpack_from('<i', raw, 1446)[0]
    dtype = {0: '<f4', 1: '<i4', 2: '<i2', 3: '<u2', 5: '<f8', 6: 'u1', 8: '<u4'}.get(struct.unpack_from('<h', raw, 108)[0])
    if not dtype or min(width, height, frames) < 1 or width * height * frames > 16_000_000:
        raise ValueError('Unsupported SPE dimensions or pixel type (limit: 16 million pixels).')
    count = width * height * frames
    if len(raw) < 4100 + count * np.dtype(dtype).itemsize:
        raise ValueError('Invalid SPE: pixel data are incomplete.')
    values = np.frombuffer(raw, dtype=dtype, offset=4100, count=count).reshape(frames, height, width)
    if mode == 'auto':
        mode = 'stack' if height == 1 and frames > 1 else 'mean'
    if mode == 'stack':
        if height != 1:
            raise ValueError('SPE stack requires single-row frames.')
        result = values[:, 0, :]
    elif mode == 'frame':
        if not 0 <= frame < frames:
            raise ValueError(f'Frame index must be between 0 and {frames-1}.')
        result = values[frame]
    elif mode == 'mean':
        result = values.mean(axis=0)
    else:
        raise ValueError('Unknown SPE reading mode.')
    return np.asarray(result, dtype=float), {'frames': frames, 'spe_mode': mode, 'spe_version': version}


def _working_scalar(values, size):
    if values.shape[::-1] == size:
        return values
    return np.asarray(Image.fromarray(values.astype('float32')).resize(size, Image.Resampling.BOX), dtype=float)


def _decode_source(source, meta, data):
    decoded, distances, config = decode_intensity(source, data)
    size=(meta['width'], meta['height'])
    return _working_scalar(decoded,size), None if distances is None else _working_scalar(distances,size), config


def palette_diagnostics(mask=None):
    if _palette_distance is None:
        return {'method': 'native_grayscale' if _source_image.ndim==2 else 'rgb_luminance'}
    values=_palette_distance[mask] if mask is not None else _palette_distance.ravel()
    return {'method':'inverse_colormap_nearest_rgb','mean_palette_distance':float(np.mean(values)),
            'p95_palette_distance':float(np.percentile(values,95))}


def image_payload(include_source=False, roi=None):
    processed=preprocess_experimental_image(_image,background_percentile=0,clip_percentile=100)
    result={'meta':_image_meta,'pixels':np.round(processed,5).ravel(),
            'palette_config':_color_config,'palette_diagnostics':palette_diagnostics()}
    if roi is not None:
        result['roi']=roi
    if include_source and _source_image.ndim==3:
        rgb=Image.fromarray(_source_image).resize((_image_meta['width'],_image_meta['height']),Image.Resampling.BOX)
        result['source_rgb']=base64.b64encode(np.asarray(rgb,dtype=np.uint8).tobytes()).decode('ascii')
    return result


def decode_image(data):
    global _image, _color_config, _palette_distance
    if _source_image is None:
        raise ValueError('Load an image first.')
    config=color_config(data) if _source_image.ndim==3 else {'source_palette':'native','palette_reverse':False}
    if config!=_color_config:
        values,distances,config=_decode_source(_source_image,_image_meta,data)
        preprocess_experimental_image(values,background_percentile=0,clip_percentile=100)
        _image,_palette_distance,_color_config=values,distances,config
    return image_payload()


def load_image(data, raw):
    global _image, _image_meta, _source_image, _color_config, _palette_distance
    if len(raw) > 32 * 1024**2:
        raise ValueError('File exceeds 32 MB. Reduce image size or frame count.')
    name=str(data.get('name','image'))[:200]
    meta={'name':name}
    if name.lower().endswith('.spe'):
        source,extra=read_spe(raw,str(data.get('spe_mode','auto')),int(data.get('frame',0)))
        meta.update(extra)
    else:
        Image.MAX_IMAGE_PIXELS=16_000_000
        try:
            with Image.open(io.BytesIO(raw)) as im:
                if im.width*im.height>16_000_000:
                    raise ValueError('Image exceeds 16 million pixels.')
                if im.mode in ('RGBA','LA') or (im.mode=='P' and 'transparency' in im.info):
                    rgba=im.convert('RGBA')
                    background=Image.new('RGBA',rgba.size,'white')
                    im=Image.alpha_composite(background,rgba).convert('RGB')
                elif im.mode not in ('1','L','I','F','I;16','I;16B','I;16L'):
                    im=im.convert('RGB')
                source=np.array(im)
        except (OSError,Image.DecompressionBombError) as e:
            raise ValueError('Could not read the image. Use PNG, TIFF, JPEG or SPE 2.x.') from e
    if source.ndim not in (2,3) or min(source.shape[:2])<16:
        raise ValueError('A 2D image of at least 16 Г— 16 pixels is required.')
    if not np.all(np.isfinite(source)):
        raise ValueError('Image contains NaN or infinite values.')
    height,width=source.shape[:2]
    scale=min(1,1024/max(width,height))
    meta.update(original_width=width,original_height=height,width=round(width*scale),
                height=round(height*scale),scale=scale,color_source=source.ndim==3)
    values,distances,config=_decode_source(source,meta,data)
    processed=preprocess_experimental_image(values,background_percentile=0,clip_percentile=100)
    cx,cy,radius=automatic_roi(processed)
    _source_image,_image,_image_meta,_palette_distance,_color_config=source,values,meta,distances,config
    return image_payload(True,dict(center_x=cx,center_y=cy,radius_px=radius))


def demo_image():
    global _image, _image_meta
    size = 256
    yy, xx = np.indices((size, size))
    rho = np.hypot(xx-127.5, yy-127.5) / 112
    values = np.where(rho <= 1, jv(0, jn_zeros(0, 3)[-1] * rho)**2, 0)
    stream = io.BytesIO()
    Image.fromarray((values*65535).astype('uint16')).save(stream, format='PNG')
    result = load_image({'name': 'Synthetic HE_1,3.png'}, stream.getvalue())
    result['roi'] = {'center_x': 127.5, 'center_y': 127.5, 'radius_px': 112}
    return result


def roi_values(data):
    if _image is None:
        raise ValueError('Load an image first.')
    height, width = _image.shape
    return dict(center_x=number(data, 'center_x', 0, width-1),
                center_y=number(data, 'center_y', 0, height-1),
                radius_px=number(data, 'radius_px', 5, max(width, height)))


def refine_roi(data):
    roi = roi_values(data)
    cx, cy, radius, quality = refine_roi_from_circular_edge(_image, **roi)
    return {'roi': dict(center_x=cx, center_y=cy, radius_px=radius), 'quality': quality}


def analysis_mask(data, roi):
    height,width=_image.shape
    enabled=data.get('region_enabled',False)
    if not isinstance(enabled,bool):
        raise ValueError('Invalid rectangular selection setting.')
    if not enabled:
        return None, {'region_enabled':False}
    angle=number(data,'region_angle',-180,180,0)
    box_width=number(data,'region_width',1,math.hypot(width,height),2*roi['radius_px'])
    box_height=number(data,'region_height',1,math.hypot(width,height),2*roi['radius_px'])
    x=number(data,'region_x',0,width-1,roi['center_x'])
    y=number(data,'region_y',0,height-1,roi['center_y'])
    yy,xx=np.indices(_image.shape,dtype=float)
    a=math.radians(angle)
    along=(xx-x)*math.cos(a)+(yy-y)*math.sin(a)
    across=-(xx-x)*math.sin(a)+(yy-y)*math.cos(a)
    mask=(np.abs(along)<=box_width/2)&(np.abs(across)<=box_height/2)
    if mask.sum()<32:
        raise ValueError('Too few pixels remain inside the rectangle. Enlarge or reposition it.')
    return mask,dict(region_enabled=True,region_angle=angle,region_width=box_width,
                     region_height=box_height,region_x=x,region_y=y)


def slit_mask(data, roi):
    """Compatibility for earlier exported settings; new UI always uses a finite rectangle."""
    return analysis_mask({**data,'region_enabled':data.get('slit_enabled',False),
        'region_angle':data.get('slit_angle',0),'region_width':math.hypot(*_image.shape),
        'region_height':data.get('slit_width',30),'region_x':data.get('slit_x',roi['center_x']),
        'region_y':data.get('slit_y',roi['center_y'])},roi)


def experimental_modes(data, k0a, max_angle, count, method):
    if method == 'selected':
        terms = data.get('fit_terms')
        if not isinstance(terms, list) or not 1 <= len(terms) <= 6:
            raise ValueError('Choose between 1 and 6 modes for the selected-mode fit.')
        modes, orientations, seen = [], {}, set()
        for term in terms:
            if not isinstance(term, dict):
                raise ValueError('Invalid selected mode.')
            family = term.get('family', 'HE')
            if family not in ('HE', 'EH', 'TE', 'TM'):
                raise ValueError('Unknown selected mode family.')
            n = number(term, 'n', 0 if family in ('TE', 'TM') else 1,
                       0 if family in ('TE', 'TM') else 30, integer=True)
            m = number(term, 'm', 1, 60, integer=True)
            orientation = term.get('orientation', 'both')
            if orientation not in ('both', 'c', 's'):
                raise ValueError('Unknown selected mode orientation.')
            u = bessel_seed(family, n, m)
            if u >= k0a:
                raise ValueError(f'{family}_{n},{m} is outside the propagating range.')
            mode = Mode(family, n, m, u, 1+0j, True, 0)
            if mode.name in seen:
                raise ValueError(f'{mode.name} is already in the selected basis.')
            seen.add(mode.name)
            modes.append(mode)
            orientations[mode.name] = (('',) if family in ('TE', 'TM') else
                                       ('c', 's') if orientation == 'both' else (orientation,))
        return modes, orientations
    u_cap = min(k0a * math.sin(math.radians(max_angle)), 1.6*math.sqrt(2*count)+8)
    modes = []
    for q in range(int(u_cap)+1):
        roots = jn_zeros(q, max(8, math.ceil(u_cap/math.pi)+8))
        for m, u in enumerate(roots, start=1):
            if u > u_cap:
                break
            families = [('HE', q+1)]
            if q >= 2:
                families.append(('EH', q-1))
            if q == 0:
                families.append(('TM', 0))
            if q == 1:
                families.append(('TE', 0))
            for family, n in families:
                modes.append(Mode(family, n, m, float(u), 1+0j, True, 0))
    modes.sort(key=lambda mode: (mode.u_seed, mode.family))
    return modes[:count], {}


def analyse_image(data, progress=lambda *_: None):
    started = time.perf_counter()
    if 'source_palette' in data:
        decode_image(data)
    roi = roi_values(data)
    wavelength = number(data, 'wavelength_nm', 350, 2000, 800)
    radius_um = number(data, 'radius_um', 5, 500, 150)
    max_angle = number(data, 'max_angle', .1, 30, 5)
    count = number(data, 'catalogue', 20, 1500, 300, integer=True)
    background = number(data, 'background', 0, 30, 0)
    method = data.get('fit_mode', 'auto' if data.get('coherent', False) else 'single')
    if method not in ('single', 'auto', 'selected'):
        raise ValueError('Unknown experimental analysis method.')
    mask, mask_config = (analysis_mask(data,roi) if 'region_enabled' in data else slit_mask(data,roi))
    k0a = 2*math.pi * radius_um*1000/wavelength
    modes, orientations = experimental_modes(data, k0a, max_angle, count, method)
    if not modes:
        raise ValueError('No modes in the selected range. Increase the maximum angle.')
    samples = max(128 if mask is not None else 80, math.ceil(4*max(m.u_seed for m in modes)/math.pi+1))
    if samples > 256:
        raise ValueError('The selected mode orders require more than 256 samples. Reduce the indices.')
    progress(.03, 'Sampling the selected rectangle and waveguide region')
    processed = preprocess_experimental_image(_image, background_percentile=background,
                                               clip_percentile=100, valid_mask=mask)
    grid, sampled, visible = _sample_camera_on_grid(processed, **roi, samples=samples, valid_mask=mask)
    coverage = float(visible.sum()/grid.core_mask.sum())
    if coverage < .01 or visible.sum() < 128:
        raise ValueError('Too little of the ROI remains for fitting. Enlarge or reposition the rectangle / ROI.')
    target = sampled[visible]
    if np.max(target)-np.min(target) < 1e-10:
        raise ValueError('No resolvable intensity structure in the selected region.')
    radial, _ = polar_diagnostics(processed, **roi, valid_mask=mask)
    angles = {m.name: math.degrees(math.asin(m.u_seed/k0a)) for m in modes}
    ranked, diagnostics = _rank_single_mode_similarity(
        modes, radial, grid, sampled, visible, angles,
        require_center_maximum=bool(data.get('require_center', False)) if method != 'selected' else False,
        progress=lambda f, _: progress(.15+.55*f, 'Comparing modes inside the measured region'))
    top = ranked[:5]
    rows = [{**{k: v for k, v in row.items() if k != 'mode'}, 'name': row['mode'].name} for row in top]
    best = top[0]['mode']
    field = _profile_components(best, grid, 1., 'c')
    prediction = np.abs(field.Ex)**2 + np.abs(field.Ey)**2
    prediction *= float(np.dot(prediction[visible], target)/max(np.dot(prediction[visible], prediction[visible]), 1e-300))
    fit_meta = None
    if method in ('auto', 'selected'):
        progress(.72, 'Fitting selected fields · three initial guesses')
        if method == 'selected':
            selected = modes
        else:
            selected, signatures = [], set()
            for item in ranked:
                m = item['mode']
                signature = (round(m.u_seed, 9), 0 if m.family == 'HE' and m.n == 1 else m.family)
                if signature not in signatures:
                    selected.append(m)
                    signatures.add(signature)
                if len(selected) == 4:
                    break
        fields, names, normalizations = [], [], []
        for m in selected:
            for orientation in orientations.get(m.name, ('',) if m.family in ('TE', 'TM') else ('c', 's')):
                f = _profile_components(m, grid, 1., orientation)
                scale = math.sqrt(float(np.mean((abs(f.Ex)**2+abs(f.Ey)**2)[visible])))
                if scale > 1e-12:
                    fields.append((f.Ex.real/scale, f.Ey.real/scale))
                    names.append(m.name+orientation)
                    normalizations.append(scale)
        if not fields:
            raise ValueError('The selected fields vanish inside the measured region.')
        ex = np.column_stack([f[0][visible] for f in fields])
        ey = np.column_stack([f[1][visible] for f in fields])
        fits = []
        for seed in range(3):
            fits.append(_coherent_fit(ex, ey, target.copy(), max_nfev=120, seed=seed))
            progress(.74+.075*(seed+1), f'Coherent fit · {seed+1}/3')
        fits.sort(key=lambda fit: fit[2])
        coeff, _, residual, correlation = fits[0]
        fx = sum(c*f[0] for c, f in zip(coeff, fields))
        fy = sum(c*f[1] for c, f in zip(coeff, fields))
        prediction = abs(fx)**2+abs(fy)**2
        power_scale = float(np.dot(prediction[visible], target)/max(np.dot(prediction[visible], prediction[visible]), 1e-300))
        prediction *= power_scale
        coeff *= math.sqrt(max(power_scale, 0))
        phase_ref = np.angle(coeff[int(np.argmax(abs(coeff)))])
        coeff *= np.exp(-1j*phase_ref)
        fit_meta = {'residual': residual, 'correlation': correlation, 'profiles': names,
                    'modes': [m.name for m in selected], 'method': method,
                    'coefficients': [{'name': name, 'real': c.real, 'imaginary': c.imag,
                                      'amplitude': abs(c), 'phase_deg': math.degrees(np.angle(c)),
                                      'profile_rms': scale}
                                     for name, c, scale in zip(names, coeff, normalizations)],
                    'restart_residuals': [f[2] for f in fits], 'restarts': 3}
    rho = np.array([r['rho_over_radius'] for r in radial])
    order = 1 if best.family in ('TE', 'TM') else (best.n-1 if best.family == 'HE' else best.n+1)
    predicted_radial = jv(order, best.u_seed*rho)**2
    observed_radial = np.array([r['mean_intensity'] for r in radial])
    prediction[~visible] = np.nan
    display = np.where(visible, sampled, np.nan)
    progress(1, 'Analysis complete')
    return {'rows': rows, 'diagnostics': diagnostics, 'coverage': coverage,
            'palette_decoding': palette_diagnostics(mask),
            'config': {**roi, **mask_config, **_color_config, 'wavelength_nm': wavelength, 'radius_um': radius_um,
                       'max_angle': max_angle, 'catalogue': count, 'background': background,
                       'fit_mode': method, 'fit_terms': data.get('fit_terms', []) if method == 'selected' else [],
                       'require_center': bool(data.get('require_center', False))},
            'image_meta': _image_meta, 'size': samples, 'observed': display.ravel(),
            'predicted': prediction.ravel(), 'difference': np.where(visible, sampled-prediction, np.nan).ravel(),
            'radial': {'rho': rho, 'observed': observed_radial/max(float(np.nanmax(observed_radial)), 1e-300),
                       'best_single': predicted_radial/max(float(np.max(predicted_radial)), 1e-300)},
            'fit': fit_meta, 'seconds': time.perf_counter()-started}



def mode_lab(data, progress=lambda *_: None):
    """Unit-power vector profiles, summed with user-specified complex amplitudes.

    This calculation is independent of the Gaussian projection and never replaces
    its worker state. Amplitudes refer to z=0; common phase is removed at output.
    """
    cfg = WaveguideConfig(wavelength=number(data, 'wavelength_nm', 350, 2000, 800)*1e-9,
                          diameter=number(data, 'diameter_um', 10, 1000, 300)*1e-6,
                          metal_epsilon=complex(number(data, 'epsilon_real', -1000, -.1, -31.021),
                                                number(data, 'epsilon_imag', .00001, 1000, .40948)))
    samples = number(data, 'samples', 48, 256, 128, integer=True)
    z = number(data, 'z_cm', 0, 200, 0)/100
    terms = data.get('terms')
    if not isinstance(terms, list) or not 1 <= len(terms) <= 12:
        raise ValueError('Add between 1 and 12 profiles to the mixture.')
    grid = make_grid(cfg.radius, samples)
    fields, coefficients, modes, rows = [], [], [], []
    cache = {}
    for i, term in enumerate(terms):
        if not isinstance(term, dict):
            raise ValueError('Invalid modal term.')
        family = term.get('family', 'HE')
        if family not in ('HE','EH','TE','TM'):
            raise ValueError('Unknown mode family.')
        n = number(term, 'n', 0 if family in ('TE','TM') else 1, 0 if family in ('TE','TM') else 30, integer=True)
        m = number(term, 'm', 1, 60, integer=True)
        orientation = '' if family in ('TE','TM') else term.get('orientation','c')
        if orientation not in ('','c','s'):
            raise ValueError('Orientation must be c or s.')
        amplitude = number(term, 'amplitude', 0, 1000, 1)
        phase = number(term, 'phase_deg', -36000, 36000, 0)
        u = bessel_seed(family, n, m)
        if u >= cfg.k0 * cfg.radius:
            raise ValueError(f'{family}_{n},{m} is beyond the propagating range for this geometry.')
        required = max(math.ceil(4*u/math.pi+1), 4*n+1)
        if samples < required:
            raise ValueError(f'{family}_{n},{m} requires at least {required} grid samples. Increase resolution or reduce the indices (maximum grid: 256).')
        key = (family,n,m)
        progress(.05+.8*i/len(terms), f'Building profile {i+1} of {len(terms)}')
        if key not in cache:
            mode = solve_mode(family,n,m,cfg)
            fallback = not mode.converged
            if fallback:
                mode = replace(mode, gamma=complex(math.sqrt(cfg.k0**2-(u/cfg.radius)**2),
                                                     _marcatili_amplitude_guess(family,u,cfg)))
            cache[key] = mode, fallback
        mode, fallback = cache[key]
        field = _profile_components(mode,grid,cfg.radius,orientation)
        norm = math.sqrt(field_power(field,grid))
        if not math.isfinite(norm) or norm <= 0:
            raise ValueError('The selected profile cannot be normalized.')
        field.Ex /= norm; field.Ey /= norm
        fields.append(field); modes.append(mode)
        coefficients.append(amplitude*np.exp(1j*math.radians(phase)))
        rows.append(dict(name=mode.name+orientation,u=u,neff=mode.beta/cfg.k0,
                         alpha_power_per_m=mode.power_attenuation, fallback=fallback))
    if not any(abs(c)>0 for c in coefficients):
        raise ValueError('At least one amplitude must be nonzero.')
    carrier = max(m.beta for m in modes)
    ex = np.zeros_like(grid.X,dtype=complex); ey = ex.copy()
    ex0=ex.copy(); ey0=ey.copy()
    for c, f, mode in zip(coefficients,fields,modes):
        propagator=np.exp(1j*(mode.gamma-carrier)*z)
        ex += c*f.Ex*propagator; ey += c*f.Ey*propagator
        ex0 += c*f.Ex; ey0 += c*f.Ey
    initial = field_power(Field2D(ex0,ey0),grid)
    power = field_power(Field2D(ex,ey),grid)
    weight = sum(abs(c)**2 for c in coefficients)
    cancelled = power <= 1e-20 * weight
    if cancelled: ex[:]=0; ey[:]=0; power=0.
    payload=field_payload(Field2D(ex,ey),grid)
    payload['z_cm']=z*100
    return dict(field=payload,rows=rows,power=power,initial_power=initial,
                power_ratio=power/initial if initial>1e-20*weight else None,
                cancelled=cancelled,coefficient_norm=weight)


def dispatch(action, data=None, raw=None, progress=lambda *_: None):
    data = data or {}
    functions = {'simulate': lambda: simulate(data, progress), 'slice': lambda: slice_field(data),
                 'image': lambda: load_image(data, raw), 'demo_image': demo_image,
                 'decode_image': lambda: decode_image(data),
                 'refine': lambda: refine_roi(data), 'analyse': lambda: analyse_image(data, progress),
                 'mode_lab': lambda: mode_lab(data, progress)}
    if action not in functions:
        raise ValueError('Unknown operation.')
    return json.dumps(clean(functions[action]()), ensure_ascii=False, allow_nan=False, separators=(',', ':'))
