from __future__ import annotations

from dataclasses import dataclass
import csv
import hashlib
import json
import math
import pickle
import time
from pathlib import Path

import numpy as np
from scipy.special import jn_zeros, jv

from .config import BeamConfig, WaveguideConfig
from .cylindrical_modes import ModeSpec


@dataclass(frozen=True)
class AngularWindow:
    theta_eff_deg: float
    k_perp: float
    u_target: float
    delta_u: float
    u_min: float
    u_max: float
    q_max: int
    waist: float
    cutoff_u: float


def beam_from_angle_offset(
    cfg: WaveguideConfig,
    *,
    theta_deg: float,
    tilt_azimuth_deg: float = 0.0,
    offset_um: float = 0.0,
    offset_azimuth_deg: float = 0.0,
    waist: float | None = None,
    polarization_x: complex = 1.0 + 0.0j,
    polarization_y: complex = 0.0 + 0.0j,
) -> BeamConfig:
    theta = math.radians(theta_deg)
    tilt_azimuth = math.radians(tilt_azimuth_deg)
    transverse = math.sin(theta)
    tilt_x = math.asin(transverse * math.cos(tilt_azimuth))
    tilt_y = math.asin(transverse * math.sin(tilt_azimuth))

    offset = offset_um * 1e-6
    offset_azimuth = math.radians(offset_azimuth_deg)
    return BeamConfig(
        waist=waist,
        offset_x=offset * math.cos(offset_azimuth),
        offset_y=offset * math.sin(offset_azimuth),
        tilt_x=tilt_x,
        tilt_y=tilt_y,
        polarization_x=polarization_x,
        polarization_y=polarization_y,
    )


def mode_angle_deg(cfg: WaveguideConfig, u_seed: float) -> float:
    ratio = min(1.0, max(0.0, u_seed / (cfg.k0 * cfg.radius)))
    return math.degrees(math.asin(ratio))


def beam_k_perp(cfg: WaveguideConfig, beam: BeamConfig) -> float:
    kx = cfg.k0 * math.sin(beam.tilt_x)
    ky = cfg.k0 * math.sin(beam.tilt_y)
    return math.hypot(kx, ky)


def angular_selection_window(
    cfg: WaveguideConfig,
    beam: BeamConfig,
    *,
    min_power_fraction: float = 1e-7,
    angular_extent_factor: float = 1.0,
    q_margin: int = 4,
) -> AngularWindow:
    waist = beam.resolved_waist(cfg)
    k_perp = beam_k_perp(cfg, beam)
    cutoff_u = cfg.k0 * cfg.radius
    theta_eff = math.asin(min(1.0, k_perp / cfg.k0))
    u_target = cfg.radius * k_perp
    extent = max(float(angular_extent_factor), 1e-6)
    delta_u = extent * cfg.radius * math.sqrt(2.0 * math.log(1.0 / min_power_fraction)) / waist
    u_min = max(0.0, u_target - delta_u)
    u_max = min(cutoff_u * (1.0 - 1e-8), u_target + delta_u)

    offset_r = math.hypot(beam.offset_x, beam.offset_y)
    # The azimuthal spectrum is controlled by the largest radius at which the
    # beam still carries relevant power, not by one waist.  Using k_perp*w
    # truncates the central high-q branches of a strongly tilted beam.
    beam_support = extent * waist * math.sqrt(0.5 * math.log(1.0 / min_power_fraction))
    support_radius = min(cfg.radius, offset_r + beam_support)
    phase_q = k_perp * support_radius
    offset_q = 2.0 * support_radius * offset_r / waist**2
    q_estimate = phase_q + offset_q
    transition_margin = 3.0 * q_estimate ** (1.0 / 3.0) if q_estimate > 1.0 else 0.0
    q_max = max(1, int(math.ceil(q_estimate + transition_margin + q_margin)))
    q_max = min(q_max, int(math.ceil(u_max)) + q_margin)

    return AngularWindow(
        theta_eff_deg=math.degrees(theta_eff),
        k_perp=k_perp,
        u_target=u_target,
        delta_u=delta_u,
        u_min=u_min,
        u_max=u_max,
        q_max=q_max,
        waist=waist,
        cutoff_u=cutoff_u,
    )


def _zeros_in_window(order: int, u_min: float, u_max: float) -> list[tuple[int, float]]:
    if order < 0 or u_max <= 0.0 or order > u_max + 1.0:
        return []
    count = max(
        8,
        int(math.ceil((u_max - min(order, u_max)) / math.pi + 12.0 + 2.0 * max(order, 1) ** (1.0 / 3.0))),
    )
    while True:
        zeros = jn_zeros(order, count)
        if zeros[-1] > u_max or count > 10000:
            break
        count = int(count * 1.5) + 8
    return [(idx, float(value)) for idx, value in enumerate(zeros, start=1) if u_min <= value <= u_max]


def angular_candidate_mode_specs(
    cfg: WaveguideConfig,
    beam: BeamConfig,
    *,
    min_power_fraction: float = 1e-7,
    angular_extent_factor: float = 1.0,
    q_margin: int = 4,
    include_te_tm: bool = True,
    include_he: bool = True,
    include_eh: bool = True,
    min_candidate_modes: int = 0,
    progress_callback=None,
) -> tuple[list[ModeSpec], list[dict], dict[str, float], AngularWindow]:
    started_at = time.perf_counter()
    if progress_callback is not None:
        progress_callback(0.0, "building initial angular candidate window")
    window = angular_selection_window(
        cfg,
        beam,
        min_power_fraction=min_power_fraction,
        angular_extent_factor=angular_extent_factor,
        q_margin=q_margin,
    )
    specs: list[ModeSpec] = []
    rows: list[dict] = []
    u_by_name: dict[str, float] = {}
    seen: set[str] = set()
    zero_cache: dict[int, list[tuple[int, float]]] = {}

    def cached_zeros(order: int) -> list[tuple[int, float]]:
        if order not in zero_cache:
            zero_cache[order] = _zeros_in_window(order, window.u_min, window.u_max)
        return zero_cache[order]

    def add_spec(family: str, n: int, m: int, u_seed: float, bessel_order: int, q: int) -> None:
        spec = ModeSpec(family, n, m)
        if spec.name in seen:
            return
        seen.add(spec.name)
        specs.append(spec)
        u_by_name[spec.name] = u_seed
        rows.append(
            {
                "mode": spec.name,
                "family": family,
                "n": n,
                "m": m,
                "q": q,
                "bessel_order": bessel_order,
                "u_seed": u_seed,
                "theta_mode_deg": mode_angle_deg(cfg, u_seed),
                "abs_u_minus_target": abs(u_seed - window.u_target),
            }
        )

    if include_te_tm:
        for m, u_seed in cached_zeros(1):
            add_spec("TE", 0, m, u_seed, bessel_order=1, q=1)
        for m, u_seed in cached_zeros(0):
            add_spec("TM", 0, m, u_seed, bessel_order=0, q=1)

    if include_he:
        for q in range(0, window.q_max + 1):
            for m, u_seed in cached_zeros(q):
                add_spec("HE", q + 1, m, u_seed, bessel_order=q, q=q)

    if include_eh:
        for q in range(2, window.q_max + 1):
            for m, u_seed in cached_zeros(q):
                add_spec("EH", q - 1, m, u_seed, bessel_order=q, q=q)

    rows.sort(key=lambda row: (row["abs_u_minus_target"], row["q"], row["family"], row["m"]))
    best = (specs, rows, u_by_name, window)
    target = max(0, int(min_candidate_modes))
    if progress_callback is not None:
        initial_fraction = 1.0 if target <= 0 else min(len(specs) / target, 1.0)
        progress_callback(initial_fraction, f"candidate window: {len(specs)}/{target or len(specs)} modes")
    if len(specs) < target:
        factor = max(float(angular_extent_factor), 1e-3)
        initial_count = len(specs)
        for expansion_index in range(1, 17):
            factor *= 1.35
            expanded = angular_candidate_mode_specs(
                cfg,
                beam,
                min_power_fraction=min_power_fraction,
                angular_extent_factor=factor,
                q_margin=q_margin,
                include_te_tm=include_te_tm,
                include_he=include_he,
                include_eh=include_eh,
                min_candidate_modes=0,
                progress_callback=None,
            )
            if len(expanded[0]) > len(best[0]):
                best = expanded
            if progress_callback is not None:
                elapsed = time.perf_counter() - started_at
                gained = max(len(best[0]) - initial_count, 0)
                remaining = max(target - len(best[0]), 0)
                eta = elapsed * remaining / max(gained, 1)
                progress_callback(
                    min(len(best[0]) / max(target, 1), 0.99),
                    f"candidate expansion {expansion_index}: {len(best[0])}/{target} modes, eta {eta:.1f}s",
                )
            if len(best[0]) >= target:
                break
            expanded_window = expanded[3]
            if expanded_window.u_max >= expanded_window.cutoff_u * (1.0 - 2e-8):
                break
        return best
    return best


def _bessel_order_for_spec(spec: ModeSpec) -> int:
    family = spec.family.upper()
    if family in {"TE", "TM"}:
        return 1
    if family == "HE":
        return spec.n - 1
    if family == "EH":
        return spec.n + 1
    raise ValueError(f"Unknown mode family: {spec.family}")


def estimate_excitation_polar_quadrature(
    cfg: WaveguideConfig,
    beam: BeamConfig,
    specs: list[ModeSpec],
    u_by_name: dict[str, float],
    *,
    radial_samples: int = 384,
    angular_samples: int = 512,
    min_power_fraction: float = 1e-7,
    max_modes: int | None = None,
    progress_every: int | None = 25,
    progress_callback=None,
) -> tuple[list[ModeSpec], list[dict], float]:
    """Rough modal excitation for centered or offset Gaussian beams.

    This is a polar quadrature. It is slower than the centered analytic radial
    integral, but it works for a beam entering away from the capillary center.
    """

    a = cfg.radius
    waist = beam.resolved_waist(cfg)
    nodes, weights = np.polynomial.legendre.leggauss(radial_samples)
    rho = 0.5 * (nodes + 1.0)
    wr = 0.5 * weights
    phi = np.linspace(0.0, 2.0 * np.pi, angular_samples, endpoint=False)
    dphi = 2.0 * np.pi / angular_samples

    R = a * rho[:, None]
    X = R * np.cos(phi)[None, :]
    Y = R * np.sin(phi)[None, :]
    kx = cfg.k0 * math.sin(beam.tilt_x)
    ky = cfg.k0 * math.sin(beam.tilt_y)
    envelope = np.exp(-((X - beam.offset_x) ** 2 + (Y - beam.offset_y) ** 2) / waist**2)
    phase = np.exp(1j * (kx * X + ky * Y))
    scalar = envelope * phase
    Ex = complex(beam.polarization_x) * scalar
    Ey = complex(beam.polarization_y) * scalar
    radial_weight = wr * rho
    input_power = float(a**2 * dphi * np.sum(radial_weight[:, None] * (np.abs(Ex) ** 2 + np.abs(Ey) ** 2)))
    if input_power <= 0.0:
        raise ValueError("Input power is zero in polar quadrature.")

    orders = sorted({_bessel_order_for_spec(spec) for spec in specs})
    projections: dict[int, dict[str, np.ndarray]] = {}
    started_at = time.perf_counter()
    last_report_at = started_at

    for idx, q in enumerate(orders, start=1):
        cos_q = np.cos(q * phi)
        sin_q = np.sin(q * phi)
        projections[q] = {
            "Cx": Ex @ cos_q * dphi,
            "Sx": Ex @ sin_q * dphi,
            "Cy": Ey @ cos_q * dphi,
            "Sy": Ey @ sin_q * dphi,
        }
        now = time.perf_counter()
        should_report = now - last_report_at >= 0.5 or idx == len(orders)
        if should_report:
            elapsed = time.perf_counter() - started_at
            remaining = len(orders) - idx
            eta = elapsed * remaining / max(idx, 1)
            message = f"angular projections {idx}/{len(orders)} orders, eta {eta:.1f}s"
            if progress_callback is not None:
                progress_callback(0.45 * idx / max(len(orders), 1), message)
            if progress_every is not None and progress_every > 0 and (idx % progress_every == 0 or idx == len(orders)):
                print(f"polar {message}")
            last_report_at = now

    specs_by_group: dict[tuple[str, int], list[ModeSpec]] = {}
    for spec in specs:
        specs_by_group.setdefault((spec.family.upper(), _bessel_order_for_spec(spec)), []).append(spec)

    mode_rows: list[dict] = []
    processed = 0
    radial_started_at = time.perf_counter()
    last_report_at = radial_started_at
    for (family, q), group in specs_by_group.items():
        proj = projections[q]
        if family == "TE":
            angular_by_orientation = [("", -proj["Sx"] + proj["Cy"])]
        elif family == "TM":
            angular_by_orientation = [("", proj["Cx"] + proj["Sy"])]
        elif family == "HE":
            angular_by_orientation = [("c", proj["Cx"] - proj["Sy"]), ("s", proj["Sx"] + proj["Cy"])]
        elif family == "EH":
            angular_by_orientation = [("c", proj["Cx"] + proj["Sy"]), ("s", proj["Sx"] - proj["Cy"])]
        else:
            raise ValueError(f"Unknown mode family: {family}")

        u_values = np.array([u_by_name[spec.name] for spec in group], dtype=float)
        radial_modes = jv(q, u_values[:, None] * rho[None, :])
        norms = np.sqrt(2.0 * np.pi * a**2 * np.sum(radial_modes**2 * radial_weight[None, :], axis=1))
        fractions_by_mode = np.zeros(len(group), dtype=float)
        best_by_mode = np.zeros(len(group), dtype=float)
        for orientation, angular_projection in angular_by_orientation:
            integrals = a**2 * (radial_modes @ (radial_weight * angular_projection))
            coeffs = integrals / norms
            fractions = np.abs(coeffs) ** 2 / input_power
            fractions_by_mode += fractions
            best_by_mode = np.maximum(best_by_mode, fractions)

        for spec, fraction, best_fraction, u_seed in zip(group, fractions_by_mode, best_by_mode, u_values):
            mode_rows.append(
                {
                    "mode": spec.name,
                    "family": spec.family,
                    "n": spec.n,
                    "m": spec.m,
                    "u_seed": float(u_seed),
                    "theta_mode_deg": mode_angle_deg(cfg, float(u_seed)),
                    "estimated_power_fraction": float(fraction),
                    "best_profile_fraction": float(best_fraction),
                }
            )
        processed += len(group)
        now = time.perf_counter()
        should_report = now - last_report_at >= 0.5 or processed >= len(specs)
        if should_report:
            radial_fraction = processed / max(len(specs), 1)
            elapsed_radial = max(now - radial_started_at, 1e-9)
            eta = elapsed_radial * (len(specs) - processed) / max(processed, 1)
            message = f"radial overlaps {processed}/{len(specs)} modes, eta {eta:.1f}s"
            if progress_callback is not None:
                progress_callback(0.45 + 0.55 * radial_fraction, message)
            if progress_every is not None and progress_every > 0 and (
                processed % max(1, progress_every) == 0 or processed >= len(specs)
            ):
                print(f"polar {message}")
            last_report_at = now

    mode_rows.sort(key=lambda row: row["estimated_power_fraction"], reverse=True)
    selected = [row for row in mode_rows if row["estimated_power_fraction"] >= min_power_fraction]
    if max_modes is not None:
        selected = selected[:max_modes]
    spec_by_name = {spec.name: spec for spec in specs}
    selected_specs = [spec_by_name[row["mode"]] for row in selected if row["mode"] in spec_by_name]
    return selected_specs, mode_rows, input_power


def _stable_hash(payload: dict, *, length: int = 16) -> str:
    text = json.dumps(payload, sort_keys=True, ensure_ascii=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:length]


def _cache_path(cache_dir: Path, key: str) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f"{key}.pkl"


def cached_polar_rough(
    cfg: WaveguideConfig,
    beam: BeamConfig,
    *,
    cache_dir: Path,
    min_power_fraction: float = 1e-7,
    angular_extent_factor: float = 1.0,
    q_margin: int = 4,
    include_te_tm: bool = True,
    include_he: bool = True,
    include_eh: bool = True,
    radial_samples: int = 384,
    angular_samples: int = 512,
    max_modes: int | None = None,
    min_candidate_modes: int = 0,
    force_recompute: bool = False,
    progress_callback=None,
) -> dict:
    specs, candidate_rows, u_by_name, window = angular_candidate_mode_specs(
        cfg,
        beam,
        min_power_fraction=min_power_fraction,
        angular_extent_factor=angular_extent_factor,
        q_margin=q_margin,
        include_te_tm=include_te_tm,
        include_he=include_he,
        include_eh=include_eh,
        min_candidate_modes=min_candidate_modes,
        progress_callback=(
            (lambda fraction, message: progress_callback(0.05 * fraction, message))
            if progress_callback is not None
            else None
        ),
    )
    required_angular_samples = 2 * window.q_max + 1
    effective_angular_samples = max(int(angular_samples), required_angular_samples)
    effective_angular_samples = int(math.ceil(effective_angular_samples / 32.0) * 32)
    if progress_callback is not None and effective_angular_samples != angular_samples:
        progress_callback(
            0.05,
            f"angular quadrature raised {angular_samples}->{effective_angular_samples} for q_max={window.q_max}",
        )
    key = _stable_hash(
        {
            "kind": "polar_rough_v1",
            "wavelength": cfg.wavelength,
            "diameter": cfg.diameter,
            "epsilon": [cfg.metal_epsilon.real, cfg.metal_epsilon.imag],
            "beam": {
                "waist": beam.resolved_waist(cfg),
                "offset_x": beam.offset_x,
                "offset_y": beam.offset_y,
                "tilt_x": beam.tilt_x,
                "tilt_y": beam.tilt_y,
                "polx": [complex(beam.polarization_x).real, complex(beam.polarization_x).imag],
                "poly": [complex(beam.polarization_y).real, complex(beam.polarization_y).imag],
            },
            "candidate_specs": [spec.name for spec in specs],
            "u_by_name": {name: u_by_name[name] for name in sorted(u_by_name)},
            "radial_samples": radial_samples,
            "angular_samples": effective_angular_samples,
        }
    )
    path = _cache_path(cache_dir, key)
    if path.exists() and not force_recompute:
        with path.open("rb") as handle:
            cached = pickle.load(handle)
        print(f"loaded polar rough cache: {path}")
        if progress_callback is not None:
            progress_callback(1.0, f"loaded rough cache: {path.name}")
        return cached

    selected_specs, mode_rows, input_power = estimate_excitation_polar_quadrature(
        cfg,
        beam,
        specs,
        u_by_name,
        radial_samples=radial_samples,
        angular_samples=effective_angular_samples,
        min_power_fraction=min_power_fraction,
        max_modes=max_modes,
        progress_callback=(
            (lambda fraction, message: progress_callback(0.05 + 0.95 * fraction, message))
            if progress_callback is not None
            else None
        ),
    )
    result = {
        "specs": specs,
        "candidate_rows": candidate_rows,
        "u_by_name": u_by_name,
        "window": window,
        "selected_specs": selected_specs,
        "rough_mode_rows": mode_rows,
        "input_power": input_power,
        "angular_samples_used": effective_angular_samples,
    }
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("wb") as handle:
        pickle.dump(result, handle, protocol=pickle.HIGHEST_PROTOCOL)
    tmp.replace(path)
    print(f"saved polar rough cache: {path}")
    return result


def rough_cumulative_power(rows: list[dict], count: int) -> float:
    if not rows:
        return 0.0
    values = [float(row["estimated_power_fraction"]) for row in rows[:count]]
    return float(np.sum(values))


def rough_score_fraction(rows: list[dict], count: int) -> float:
    total = rough_cumulative_power(rows, len(rows))
    if total <= 0.0:
        return 0.0
    return rough_cumulative_power(rows, count) / total


def modal_period_metrics_from_rows(
    cfg: WaveguideConfig,
    rough_mode_rows: list[dict],
    *,
    top_modes: int = 500,
    z_max_m: float = 0.5,
    z_points: int = 4000,
    min_peak_z_m: float = 0.002,
) -> dict:
    rows = [row for row in rough_mode_rows if float(row["estimated_power_fraction"]) > 0.0][:top_modes]
    total_rough_score = rough_cumulative_power(rough_mode_rows, len(rough_mode_rows))
    top_rough_score = rough_cumulative_power(rough_mode_rows, len(rows))
    top_score_fraction = top_rough_score / total_rough_score if total_rough_score > 0.0 else 0.0
    if len(rows) < 2:
        return {
            "top_modes_used": len(rows),
            "top_power_fraction": top_rough_score,
            "top_score_fraction_of_total": top_score_fraction,
            "rough_total_power_fraction": total_rough_score,
            "beta_mean": math.nan,
            "beta_std": 0.0,
            "coherence_length_m": math.inf,
            "first_peak_z_m": math.nan,
            "first_peak_value": math.nan,
            "best_peak_z_m": math.nan,
            "best_peak_value": math.nan,
        }

    weights = np.array([float(row["estimated_power_fraction"]) for row in rows], dtype=float)
    weights = weights / np.sum(weights)
    u = np.array([float(row["u_seed"]) for row in rows], dtype=float)
    beta = np.sqrt(np.maximum(cfg.k0**2 - (u / cfg.radius) ** 2, 0.0))
    beta_mean = float(np.sum(weights * beta))
    beta_std = float(np.sqrt(np.sum(weights * (beta - beta_mean) ** 2)))
    coherence_length = float(2.0 * np.pi / beta_std) if beta_std > 0.0 else math.inf

    z = np.linspace(0.0, z_max_m, z_points)
    phases = np.exp(1j * np.outer(z, beta - beta_mean))
    coherence = np.abs(phases @ weights) ** 2
    min_idx = int(np.searchsorted(z, min_peak_z_m))
    local = np.where((coherence[1:-1] > coherence[:-2]) & (coherence[1:-1] >= coherence[2:]))[0] + 1
    local = local[local >= min_idx]
    if len(local) > 0:
        first_idx = int(local[0])
        best_idx = int(local[np.argmax(coherence[local])])
        first_peak_z = float(z[first_idx])
        first_peak_value = float(coherence[first_idx])
        best_peak_z = float(z[best_idx])
        best_peak_value = float(coherence[best_idx])
    else:
        tail = coherence[min_idx:]
        if len(tail) == 0:
            first_peak_z = best_peak_z = math.nan
            first_peak_value = best_peak_value = math.nan
        else:
            best_rel = int(np.argmax(tail))
            best_idx = min_idx + best_rel
            first_peak_z = math.nan
            first_peak_value = math.nan
            best_peak_z = float(z[best_idx])
            best_peak_value = float(coherence[best_idx])

    return {
        "top_modes_used": len(rows),
        "top_power_fraction": top_rough_score,
        "top_score_fraction_of_total": top_score_fraction,
        "rough_total_power_fraction": total_rough_score,
        "beta_mean": beta_mean,
        "beta_std": beta_std,
        "coherence_length_m": coherence_length,
        "first_peak_z_m": first_peak_z,
        "first_peak_value": first_peak_value,
        "best_peak_z_m": best_peak_z,
        "best_peak_value": best_peak_value,
    }


def run_angle_offset_sweep(
    cfg: WaveguideConfig,
    *,
    angles_deg: list[float],
    offsets_um: list[float],
    waist: float | None,
    cache_dir: Path,
    output_csv: Path,
    tilt_azimuth_deg: float = 0.0,
    offset_azimuth_deg: float = 0.0,
    min_power_fraction: float = 1e-7,
    radial_samples: int = 384,
    angular_samples: int = 512,
    top_modes_for_period: int = 500,
    force_recompute: bool = False,
) -> list[dict]:
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    done: set[tuple[float, float]] = set()
    if output_csv.exists() and not force_recompute:
        with output_csv.open("r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                parsed = dict(row)
                rows.append(parsed)
                done.add((float(parsed["angle_deg"]), float(parsed["offset_um"])))

    fieldnames = [
        "angle_deg",
        "offset_um",
        "theta_eff_deg",
        "u_target",
        "q_max",
        "candidate_modes",
        "rough_total_power_fraction",
        "top_modes_used",
        "top_power_fraction",
        "top_score_fraction_of_total",
        "coherence_length_m",
        "first_peak_z_m",
        "first_peak_value",
        "best_peak_z_m",
        "best_peak_value",
        "transverse_phase_period_um",
    ]

    for angle in angles_deg:
        for offset in offsets_um:
            key = (float(angle), float(offset))
            if key in done:
                print(f"skip completed sweep point angle={angle:g} deg offset={offset:g} um")
                continue
            print(f"sweep point angle={angle:g} deg offset={offset:g} um")
            beam = beam_from_angle_offset(
                cfg,
                theta_deg=float(angle),
                tilt_azimuth_deg=tilt_azimuth_deg,
                offset_um=float(offset),
                offset_azimuth_deg=offset_azimuth_deg,
                waist=waist,
            )
            rough = cached_polar_rough(
                cfg,
                beam,
                cache_dir=cache_dir,
                min_power_fraction=min_power_fraction,
                radial_samples=radial_samples,
                angular_samples=angular_samples,
                force_recompute=force_recompute,
            )
            metrics = modal_period_metrics_from_rows(
                cfg,
                rough["rough_mode_rows"],
                top_modes=top_modes_for_period,
            )
            k_perp = beam_k_perp(cfg, beam)
            transverse_period_um = math.inf if k_perp <= 0.0 else 2.0 * np.pi / k_perp * 1e6
            row = {
                "angle_deg": float(angle),
                "offset_um": float(offset),
                "theta_eff_deg": rough["window"].theta_eff_deg,
                "u_target": rough["window"].u_target,
                "q_max": rough["window"].q_max,
                "candidate_modes": len(rough["specs"]),
                "rough_total_power_fraction": metrics["rough_total_power_fraction"],
                "top_modes_used": metrics["top_modes_used"],
                "top_power_fraction": metrics["top_power_fraction"],
                "top_score_fraction_of_total": metrics["top_score_fraction_of_total"],
                "coherence_length_m": metrics["coherence_length_m"],
                "first_peak_z_m": metrics["first_peak_z_m"],
                "first_peak_value": metrics["first_peak_value"],
                "best_peak_z_m": metrics["best_peak_z_m"],
                "best_peak_value": metrics["best_peak_value"],
                "transverse_phase_period_um": transverse_period_um,
            }
            rows.append(row)
            with output_csv.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            done.add(key)
            print(f"saved sweep progress: {output_csv}")
    return rows
