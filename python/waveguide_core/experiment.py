"""Numerical routines extracted from the desktop experimental module.
No GUI, file deserialization, or operating-system dependencies.
"""
from __future__ import annotations
import math
import time
from typing import Callable
import numpy as np
from scipy.ndimage import gaussian_filter, gaussian_filter1d, map_coordinates
from scipy.optimize import least_squares, minimize
from scipy.signal import find_peaks
from scipy.special import jv
from .cylindrical_modes import Mode
from .projection import make_grid
ProgressCallback = Callable[[float, str], None]

def preprocess_experimental_image(
    image: np.ndarray,
    *,
    background_percentile: float = 5.0,
    clip_percentile: float = 99.9,
    blur_sigma: float = 0.0,
    gamma: float = 1.0,
    invert: bool = False,
) -> np.ndarray:
    values = np.asarray(image, dtype=np.float64).copy()
    finite = np.isfinite(values)
    if not np.any(finite):
        raise ValueError("The source contains no finite pixels")
    values[~finite] = float(np.nanmedian(values[finite]))
    if invert:
        values = float(np.max(values)) - values
    background = float(np.percentile(values, np.clip(background_percentile, 0.0, 95.0)))
    values = np.maximum(values - background, 0.0)
    if blur_sigma > 0.0:
        values = gaussian_filter(values, sigma=float(blur_sigma), mode="nearest")
    positive = values[values > 0.0]
    if positive.size:
        ceiling = float(np.percentile(positive, np.clip(clip_percentile, 50.0, 100.0)))
        if ceiling > 0.0:
            values = np.minimum(values, ceiling) / ceiling
    maximum = float(np.max(values, initial=0.0))
    if maximum <= 0.0:
        raise ValueError("The image is empty after background subtraction")
    values /= maximum
    exponent = max(0.05, float(gamma))
    return np.power(values, exponent)


def automatic_roi(image: np.ndarray) -> tuple[float, float, float]:
    """Estimate the beam center and use the largest practical inscribed circle."""

    values = np.maximum(np.asarray(image, dtype=np.float64), 0.0)
    threshold = float(np.percentile(values, 60.0))
    weights = np.maximum(values - threshold, 0.0)
    if float(np.sum(weights)) <= 0.0:
        weights = values
    yy, xx = np.indices(values.shape, dtype=float)
    total = max(float(np.sum(weights)), 1e-300)
    cx = float(np.sum(xx * weights) / total)
    cy = float(np.sum(yy * weights) / total)
    edge_radius = min(cx, cy, values.shape[1] - 1.0 - cx, values.shape[0] - 1.0 - cy)
    if edge_radius < 8.0:
        cx = 0.5 * (values.shape[1] - 1.0)
        cy = 0.5 * (values.shape[0] - 1.0)
        edge_radius = min(cx, cy)
    return cx, cy, max(8.0, 0.96 * edge_radius)


def refine_roi_from_circular_edge(
    image: np.ndarray,
    *,
    center_x: float,
    center_y: float,
    radius_px: float,
    crop_left_x: float | None = None,
    crop_right_x: float | None = None,
    crop_top_y: float | None = None,
    crop_bottom_y: float | None = None,
) -> tuple[float, float, float, dict]:
    """Refine a roughly placed ROI by maximizing gradient on its circular wall."""

    values = np.asarray(image, dtype=np.float64)
    if values.ndim != 2 or min(values.shape) < 16:
        raise ValueError("A two-dimensional image of at least 16x16 pixels is required")
    cx0 = float(center_x)
    cy0 = float(center_y)
    radius0 = float(radius_px)
    if not all(math.isfinite(value) for value in (cx0, cy0, radius0)) or radius0 < 5.0:
        raise ValueError("Give a rough ROI center and radius before edge refinement")

    smoothed = gaussian_filter(values, sigma=1.0, mode="nearest")
    gradient_y, gradient_x = np.gradient(smoothed)
    gradient = np.hypot(gradient_x, gradient_y)
    finite_gradient = gradient[np.isfinite(gradient)]
    reference_gradient = float(np.percentile(finite_gradient, 90.0)) if finite_gradient.size else 0.0
    if reference_gradient <= 1e-14:
        raise ValueError("No usable intensity edge was found in the image")

    angles = np.linspace(-math.pi, math.pi, 720, endpoint=False)
    cos_phi = np.cos(angles)
    sin_phi = np.sin(angles)
    radial_offsets = np.linspace(-2.0, 2.0, 5)
    height, width = values.shape

    def edge_score(parameters: np.ndarray) -> tuple[float, float]:
        cx, cy, radius = (float(value) for value in parameters)
        sampled_bands: list[np.ndarray] = []
        valid_any = np.zeros(angles.shape, dtype=bool)
        for offset in radial_offsets:
            sampled_radius = max(1.0, radius + float(offset))
            xx = cx + sampled_radius * cos_phi
            yy = cy - sampled_radius * sin_phi
            valid = (xx >= 0.0) & (xx <= width - 1.0) & (yy >= 0.0) & (yy <= height - 1.0)
            if crop_left_x is not None:
                valid &= xx >= float(crop_left_x)
            if crop_right_x is not None:
                valid &= xx <= float(crop_right_x)
            if crop_top_y is not None:
                valid &= yy >= float(crop_top_y)
            if crop_bottom_y is not None:
                valid &= yy <= float(crop_bottom_y)
            samples = map_coordinates(gradient, [yy, xx], order=1, mode="constant", cval=np.nan)
            samples[~valid] = np.nan
            sampled_bands.append(samples)
            valid_any |= valid
        stacked = np.vstack(sampled_bands)
        boundary_values = np.max(np.where(np.isfinite(stacked), stacked, -np.inf), axis=0)
        boundary_values[~np.isfinite(boundary_values)] = np.nan
        boundary_values = boundary_values[np.isfinite(boundary_values)]
        coverage = float(np.count_nonzero(valid_any) / valid_any.size)
        if boundary_values.size < 24 or coverage < 0.03:
            return 0.0, coverage
        cutoff = float(np.percentile(boundary_values, 30.0))
        strong_values = boundary_values[boundary_values >= cutoff]
        score = float(np.mean(strong_values)) * math.sqrt(coverage)
        return score, coverage

    shift = max(3.0, 0.22 * radius0)
    radius_span = max(3.0, 0.22 * radius0)
    bounds = (
        (max(0.0, cx0 - shift), min(width - 1.0, cx0 + shift)),
        (max(0.0, cy0 - shift), min(height - 1.0, cy0 + shift)),
        (max(5.0, radius0 - radius_span), min(max(width, height), radius0 + radius_span)),
    )
    initial = np.asarray([cx0, cy0, radius0], dtype=float)
    initial_score, initial_coverage = edge_score(initial)

    def objective(parameters: np.ndarray) -> float:
        score, _coverage = edge_score(parameters)
        displacement = (
            ((parameters[0] - cx0) / max(shift, 1.0)) ** 2
            + ((parameters[1] - cy0) / max(shift, 1.0)) ** 2
            + ((parameters[2] - radius0) / max(radius_span, 1.0)) ** 2
        )
        return -score + 0.002 * reference_gradient * float(displacement)

    fit = minimize(
        objective,
        initial,
        method="Powell",
        bounds=bounds,
        options={"maxiter": 90, "xtol": 0.03, "ftol": 1e-5},
    )
    refined = np.asarray(fit.x, dtype=float)
    refined_score, refined_coverage = edge_score(refined)
    normalized_score = refined_score / max(reference_gradient, 1e-300)
    improvement = refined_score / max(initial_score, 1e-300)
    confidence = min(1.0, max(0.0, normalized_score)) * min(1.0, refined_coverage / 0.35)
    if refined_score <= 1e-14 or confidence < 0.08:
        raise ValueError(
            "The circular wall is too weak or too strongly cropped for reliable automatic refinement"
        )
    diagnostics = {
        "confidence": float(confidence),
        "edge_score": float(refined_score),
        "initial_edge_score": float(initial_score),
        "score_improvement": float(improvement),
        "visible_boundary_fraction": float(refined_coverage),
        "initial_visible_boundary_fraction": float(initial_coverage),
        "optimizer_success": bool(fit.success),
    }
    return float(refined[0]), float(refined[1]), float(refined[2]), diagnostics


def _sample_camera_on_grid(
    image: np.ndarray,
    center_x: float,
    center_y: float,
    radius_px: float,
    samples: int,
    *,
    crop_left_x: float | None = None,
    crop_right_x: float | None = None,
    crop_top_y: float | None = None,
    crop_bottom_y: float | None = None,
):
    grid = make_grid(1.0, samples=int(samples))
    pixel_x = float(center_x) + grid.X * float(radius_px)
    pixel_y = float(center_y) - grid.Y * float(radius_px)
    sampled = map_coordinates(image, [pixel_y, pixel_x], order=1, mode="constant", cval=0.0)
    visible = (
        grid.core_mask
        & (pixel_x >= 0.0)
        & (pixel_x <= image.shape[1] - 1.0)
        & (pixel_y >= 0.0)
        & (pixel_y <= image.shape[0] - 1.0)
    )
    if crop_left_x is not None:
        visible &= pixel_x >= float(crop_left_x)
    if crop_right_x is not None:
        visible &= pixel_x <= float(crop_right_x)
    if crop_top_y is not None:
        visible &= pixel_y >= float(crop_top_y)
    if crop_bottom_y is not None:
        visible &= pixel_y <= float(crop_bottom_y)
    sampled[~visible] = np.nan
    return grid, sampled, visible


def polar_diagnostics(
    image: np.ndarray,
    *,
    center_x: float,
    center_y: float,
    radius_px: float,
    crop_left_x: float | None = None,
    crop_right_x: float | None = None,
    crop_top_y: float | None = None,
    crop_bottom_y: float | None = None,
    radial_samples: int = 180,
    angular_samples: int = 360,
) -> tuple[list[dict], list[dict]]:
    rho = np.linspace(0.0, 1.0, max(32, int(radial_samples)))
    phi = np.linspace(-np.pi, np.pi, max(64, int(angular_samples)), endpoint=False)
    rr, pp = np.meshgrid(rho, phi, indexing="ij")
    xx = float(center_x) + float(radius_px) * rr * np.cos(pp)
    yy = float(center_y) - float(radius_px) * rr * np.sin(pp)
    polar = map_coordinates(image, [yy, xx], order=1, mode="constant", cval=0.0)
    visible = (
        (xx >= 0.0)
        & (xx <= image.shape[1] - 1.0)
        & (yy >= 0.0)
        & (yy <= image.shape[0] - 1.0)
    )
    if crop_left_x is not None:
        visible &= xx >= float(crop_left_x)
    if crop_right_x is not None:
        visible &= xx <= float(crop_right_x)
    if crop_top_y is not None:
        visible &= yy >= float(crop_top_y)
    if crop_bottom_y is not None:
        visible &= yy <= float(crop_bottom_y)
    polar[~visible] = np.nan
    radial_count = np.sum(visible, axis=1)
    radial = np.divide(
        np.nansum(polar, axis=1),
        radial_count,
        out=np.full(rho.shape, np.nan, dtype=float),
        where=radial_count > 0,
    )
    angular_denominator = np.sum(np.where(visible, rr, 0.0), axis=0)
    angular = np.divide(
        np.nansum(polar * rr, axis=0),
        angular_denominator,
        out=np.full(phi.shape, np.nan, dtype=float),
        where=angular_denominator > 0.0,
    )
    finite_angular = np.flatnonzero(np.isfinite(angular))
    if finite_angular.size < 3:
        angular = np.zeros_like(phi)
    elif finite_angular.size < angular.size:
        indices = np.arange(angular.size)
        extended_x = np.concatenate(
            [finite_angular - angular.size, finite_angular, finite_angular + angular.size]
        )
        extended_y = np.tile(angular[finite_angular], 3)
        angular = np.interp(indices, extended_x, extended_y)
    angular_centered = angular - np.mean(angular)
    spectrum = np.abs(np.fft.rfft(angular_centered)) ** 2
    spectrum /= max(float(np.sum(spectrum)), 1e-300)
    radial_rows = [
        {
            "rho_over_radius": float(r),
            "mean_intensity": float(v),
            "visible_angular_fraction": float(count / visible.shape[1]),
        }
        for r, v, count in zip(rho, radial, radial_count)
    ]
    harmonic_rows = [
        {"angular_harmonic": int(index), "power_fraction": float(value)}
        for index, value in enumerate(spectrum[: min(101, spectrum.size)])
    ]
    return radial_rows, harmonic_rows


def _radial_order(mode: Mode) -> int:
    if mode.family.upper() in {"TE", "TM"}:
        return 1
    if mode.family.upper() == "HE":
        return max(0, mode.n - 1)
    return mode.n + 1


def _profile_correlation(first: np.ndarray, second: np.ndarray) -> float:
    a = np.asarray(first, dtype=float)
    b = np.asarray(second, dtype=float)
    finite = np.isfinite(a) & np.isfinite(b)
    if np.count_nonzero(finite) < 3:
        return 0.0
    a = a[finite]
    b = b[finite]
    a = a - float(np.mean(a))
    b = b - float(np.mean(b))
    denominator = float(np.linalg.norm(a) * np.linalg.norm(b))
    return float(np.dot(a, b) / denominator) if denominator > 1e-300 else 0.0


def _ring_profile_features(rho: np.ndarray, profile: np.ndarray) -> tuple[np.ndarray, float]:
    """Return robust ring-maximum positions and their median spacing."""

    x = np.asarray(rho, dtype=float)
    y = np.asarray(profile, dtype=float)
    finite = np.isfinite(x) & np.isfinite(y)
    x = x[finite]
    y = y[finite]
    if x.size < 12 or float(np.ptp(y)) <= 1e-14:
        return np.asarray([], dtype=float), math.nan
    y = (y - float(np.min(y))) / max(float(np.ptp(y)), 1e-300)
    smooth = gaussian_filter1d(y, sigma=1.0, mode="nearest")
    trend_sigma = max(4.0, x.size / 18.0)
    trend = gaussian_filter1d(smooth, sigma=trend_sigma, mode="nearest")
    oscillatory = smooth - trend
    scale = float(np.percentile(np.abs(oscillatory), 85.0))
    prominence = max(0.008, 0.18 * scale)
    minimum_distance = max(3, x.size // 45)
    indices, _properties = find_peaks(
        oscillatory,
        prominence=prominence,
        distance=minimum_distance,
    )
    positions = x[indices]
    positions = positions[(positions >= 0.05) & (positions <= 0.98)]
    if positions.size < 2:
        indices, _properties = find_peaks(
            smooth,
            prominence=0.006,
            distance=minimum_distance,
        )
        positions = x[indices]
        positions = positions[(positions >= 0.05) & (positions <= 0.98)]
    period = float(np.median(np.diff(positions))) if positions.size >= 2 else math.nan
    return positions, period


def _ring_similarity(
    target_positions: np.ndarray,
    target_period: float,
    mode_positions: np.ndarray,
    mode_period: float,
) -> tuple[float, float, float]:
    if target_positions.size == 0 or mode_positions.size == 0:
        return 0.0, math.nan, math.nan
    target_to_mode = np.min(np.abs(target_positions[:, None] - mode_positions[None, :]), axis=1)
    mode_to_target = np.min(np.abs(mode_positions[:, None] - target_positions[None, :]), axis=1)
    peak_error = float(0.5 * (np.mean(target_to_mode) + np.mean(mode_to_target)))
    peak_score = math.exp(-peak_error / 0.045)
    count_score = math.exp(
        -abs(int(target_positions.size) - int(mode_positions.size)) / max(int(target_positions.size), 1)
    )
    if math.isfinite(target_period) and math.isfinite(mode_period) and target_period > 0.0 and mode_period > 0.0:
        relative_period_error = abs(mode_period - target_period) / target_period
        period_score = math.exp(-relative_period_error / 0.30)
    else:
        relative_period_error = math.nan
        period_score = 0.0
    score = 0.50 * peak_score + 0.35 * period_score + 0.15 * count_score
    return float(score), peak_error, relative_period_error


def _rank_single_mode_similarity(
    modes: list[Mode],
    radial_rows: list[dict],
    grid,
    sampled: np.ndarray,
    visible_mask: np.ndarray,
    modal_angles: dict[str, float],
    *,
    require_center_maximum: bool = True,
    progress: ProgressCallback | None = None,
    stop_requested: Callable[[], bool] | None = None,
) -> tuple[list[dict], dict]:
    """Rank individual mode intensities against one experimental ROI."""

    rho = np.asarray([row["rho_over_radius"] for row in radial_rows], dtype=float)
    target_profile = np.asarray([row["mean_intensity"] for row in radial_rows], dtype=float)
    finite_profile = np.isfinite(rho) & np.isfinite(target_profile)
    if np.count_nonzero(finite_profile) < 12:
        raise ValueError("Too little radial information remains for single-mode similarity search")
    rho = rho[finite_profile]
    target_profile = target_profile[finite_profile]
    target_profile -= float(np.min(target_profile))
    target_profile /= max(float(np.max(target_profile)), 1e-300)
    target_peak_positions, target_period = _ring_profile_features(rho, target_profile)
    center_mask = rho <= 0.05
    center_annulus = (rho >= 0.08) & (rho <= 0.15)
    target_center_fraction = float(np.mean(target_profile[center_mask])) if np.any(center_mask) else float(target_profile[0])
    target_center_annulus = (
        float(np.mean(target_profile[center_annulus])) if np.any(center_annulus) else target_center_fraction
    )
    target_center_is_maximum = bool(target_center_fraction >= target_center_annulus)

    target_pixels = np.asarray(sampled[visible_mask], dtype=float)
    target_pixels -= float(np.min(target_pixels))
    target_pixels /= max(float(np.max(target_pixels)), 1e-300)
    pixel_rho = np.asarray(grid.R[visible_mask], dtype=float)
    rows: list[dict] = []
    total = len(modes)
    report_every = max(1, total // 50)
    for index, mode in enumerate(modes, start=1):
        if stop_requested is not None and stop_requested():
            raise InterruptedError("experimental similarity search stopped")
        if progress is not None and (index == total or index % report_every == 0):
            progress(index / max(total, 1), f"single-mode similarity {index}/{total} modes")
        order = _radial_order(mode)
        if require_center_maximum and order != 0:
            continue
        template_profile = jv(order, float(mode.u_seed) * rho) ** 2
        template_profile /= max(float(np.max(template_profile)), 1e-300)
        exact_center_fraction = 1.0 if order == 0 else 0.0
        mode_center_fraction = (
            float(np.mean(template_profile[center_mask])) if np.any(center_mask) else exact_center_fraction
        )
        radial_correlation = _profile_correlation(target_profile, template_profile)
        radial_cosine = float(
            np.dot(target_profile, template_profile)
            / max(float(np.linalg.norm(target_profile) * np.linalg.norm(template_profile)), 1e-300)
        )
        radial_score = 0.70 * max(0.0, radial_correlation) + 0.30 * max(0.0, radial_cosine)
        mode_peak_positions, mode_period = _ring_profile_features(rho, template_profile)
        ring_score, peak_error, relative_period_error = _ring_similarity(
            target_peak_positions,
            target_period,
            mode_peak_positions,
            mode_period,
        )
        template_pixels = jv(order, float(mode.u_seed) * pixel_rho) ** 2
        template_pixels /= max(float(np.max(template_pixels)), 1e-300)
        correlation_2d = _profile_correlation(target_pixels, template_pixels)
        scale = float(
            np.dot(template_pixels, target_pixels)
            / max(float(np.dot(template_pixels, template_pixels)), 1e-300)
        )
        relative_l2 = float(
            np.linalg.norm(scale * template_pixels - target_pixels)
            / max(float(np.linalg.norm(target_pixels)), 1e-300)
        )
        center_score = math.exp(-abs(mode_center_fraction - target_center_fraction) / 0.22)
        # Ring spacing is the primary experimental observable here.  A broad
        # low-order profile can correlate well with the envelope while having
        # the wrong number of rings, so the ring term deliberately outweighs
        # the envelope-only radial correlation.
        similarity_score = (
            0.30 * radial_score
            + 0.45 * ring_score
            + 0.15 * max(0.0, correlation_2d)
            + 0.10 * center_score
        )
        rows.append(
            {
                "mode": mode,
                "similarity_score": float(similarity_score),
                "radial_correlation": float(radial_correlation),
                "radial_cosine": float(radial_cosine),
                "ring_score": float(ring_score),
                "target_period_rho": float(target_period),
                "mode_period_rho": float(mode_period),
                "period_relative_error": float(relative_period_error),
                "ring_peak_error_rho": float(peak_error),
                "target_ring_count": int(target_peak_positions.size),
                "mode_ring_count": int(mode_peak_positions.size),
                "center_score": float(center_score),
                "target_center_fraction": float(target_center_fraction),
                "mode_center_fraction": float(mode_center_fraction),
                "mode_exact_center_fraction": float(exact_center_fraction),
                "correlation_2d": float(correlation_2d),
                "relative_l2_2d": float(relative_l2),
                "modal_angle_deg": float(modal_angles.get(mode.name, math.nan)),
            }
        )
    if not rows:
        qualifier = " with a non-zero central maximum" if require_center_maximum else ""
        raise ValueError(f"No candidate modes{qualifier} remain in the selected catalogue")
    rows.sort(key=lambda row: row["similarity_score"], reverse=True)
    diagnostics = {
        "target_center_fraction": target_center_fraction,
        "target_center_annulus_fraction": target_center_annulus,
        "target_center_is_maximum": target_center_is_maximum,
        "target_period_rho": target_period,
        "target_ring_positions_rho": [float(value) for value in target_peak_positions],
        "target_ring_count": int(target_peak_positions.size),
        "ranked_modes": len(rows),
        "catalogue_modes": len(modes),
        "require_center_maximum": bool(require_center_maximum),
    }
    return rows, diagnostics


def _coherent_fit(
    ex: np.ndarray,
    ey: np.ndarray,
    target: np.ndarray,
    *,
    max_nfev: int,
    seed: int,
    progress: ProgressCallback | None = None,
    stop_requested: Callable[[], bool] | None = None,
):
    count = ex.shape[1]
    y = np.asarray(target, dtype=float)
    y /= max(float(np.mean(y)), 1e-300)
    individual = np.abs(ex) ** 2 + np.abs(ey) ** 2
    individual /= np.maximum(np.mean(individual, axis=0, keepdims=True), 1e-300)
    correlations = individual.T @ y / (
        np.maximum(np.linalg.norm(individual, axis=0), 1e-300) * max(float(np.linalg.norm(y)), 1e-300)
    )
    rng = np.random.default_rng(seed)
    amplitude = np.sqrt(np.maximum(correlations - np.percentile(correlations, 25.0), 1e-6))
    amplitude /= max(float(np.linalg.norm(amplitude)), 1e-300)
    phase = rng.uniform(-np.pi, np.pi, count)
    initial_complex = amplitude * np.exp(1j * phase)
    initial = np.concatenate([initial_complex.real, initial_complex.imag[1:]])
    residual_calls = 0
    expected_calls = max(1, int(max_nfev) * (2 * count + 1))
    report_every = max(8, count)
    started_at = time.perf_counter()

    def unpack(parameters: np.ndarray) -> np.ndarray:
        return parameters[:count] + 1j * np.concatenate([[0.0], parameters[count:]])

    def residual(parameters: np.ndarray) -> np.ndarray:
        nonlocal residual_calls
        residual_calls += 1
        if stop_requested is not None and stop_requested():
            raise InterruptedError("experimental fit stopped")
        if progress is not None and (residual_calls == 1 or residual_calls % report_every == 0):
            fraction = min(0.99, residual_calls / expected_calls)
            elapsed = time.perf_counter() - started_at
            eta = elapsed * (1.0 - fraction) / max(fraction, 1e-9)
            progress(fraction, f"fit evaluations {residual_calls}/{expected_calls} approx, eta {eta:.1f}s")
        coeff = unpack(parameters)
        fx = ex @ coeff
        fy = ey @ coeff
        intensity = np.abs(fx) ** 2 + np.abs(fy) ** 2
        scale = float(np.dot(intensity, y) / max(np.dot(intensity, intensity), 1e-300))
        return scale * intensity - y

    fit = least_squares(
        residual,
        initial,
        method="trf",
        loss="soft_l1",
        f_scale=0.15,
        max_nfev=max(20, int(max_nfev)),
    )
    coeff = unpack(fit.x)
    fx = ex @ coeff
    fy = ey @ coeff
    intensity = np.abs(fx) ** 2 + np.abs(fy) ** 2
    scale = float(np.dot(intensity, y) / max(np.dot(intensity, intensity), 1e-300))
    prediction = scale * intensity
    relative_residual = float(np.linalg.norm(prediction - y) / max(np.linalg.norm(y), 1e-300))
    correlation = float(np.corrcoef(prediction, y)[0, 1]) if np.std(prediction) > 0.0 and np.std(y) > 0.0 else 0.0
    return coeff, prediction, relative_residual, correlation
