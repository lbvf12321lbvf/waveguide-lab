from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

import numpy as np
from scipy.optimize import least_squares, root
from scipy.special import hankel1e, jn_zeros, jv

from .config import WaveguideConfig


@dataclass(frozen=True)
class ModeSpec:
    family: str
    n: int
    m: int

    @property
    def name(self) -> str:
        return f"{self.family}_{self.n},{self.m}"


@dataclass(frozen=True)
class Mode:
    family: str
    n: int
    m: int
    u_seed: float
    gamma: complex
    converged: bool
    residual: float

    @property
    def name(self) -> str:
        return f"{self.family}_{self.n},{self.m}"

    def neff(self, cfg: WaveguideConfig) -> complex:
        return self.gamma / cfg.k0

    def to_spec(self) -> ModeSpec:
        return ModeSpec(self.family, self.n, self.m)

    @property
    def beta(self) -> float:
        return float(np.real(self.gamma))

    @property
    def amplitude_attenuation(self) -> float:
        return float(np.imag(self.gamma))

    @property
    def power_attenuation(self) -> float:
        return 2.0 * self.amplitude_attenuation

    @property
    def attenuation_length(self) -> float:
        alpha = self.power_attenuation
        if alpha <= 0.0:
            return np.inf
        return 1.0 / alpha


def _radial_wavenumbers(gamma: complex, cfg: WaveguideConfig) -> tuple[complex, complex]:
    k0 = cfg.k0
    v = cfg.metal_index
    ki = np.sqrt(k0**2 - gamma**2 + 0j)
    ke = np.sqrt(v**2 * k0**2 - gamma**2 + 0j)
    return ki, ke


def hybrid_equation(gamma: complex, n: int, cfg: WaveguideConfig) -> complex:
    """Hybrid HE/EH characteristic equation from the original notebook.

    The old notebook accidentally passed the radial index as ``n`` for HE/EH
    root solving. This function always receives the azimuthal index.
    """

    a = cfg.radius
    k0 = cfg.k0
    v = cfg.metal_index
    ki, ke = _radial_wavenumbers(gamma, cfg)

    j_ratio = jv(n + 1, ki * a) / jv(n, ki * a)
    h_ratio = hankel1e(n + 1, ke * a) / hankel1e(n, ke * a)

    te = (
        n * (1.0 / (ki * a) ** 2 - 1.0 / (ke * a) ** 2)
        + h_ratio / (ke * a)
        - j_ratio / (ki * a)
    )
    tm = (
        n * (1.0 / (ki * a) ** 2 - v**2 / (ke * a) ** 2)
        + v**2 * h_ratio / (ke * a)
        - j_ratio / (ki * a)
    )
    rhs = (n * gamma / k0) ** 2 * (1.0 / (ki * a) ** 2 - 1.0 / (ke * a) ** 2) ** 2
    return (te * tm - rhs) * (ki * a) ** 2


def te_equation(gamma: complex, cfg: WaveguideConfig) -> complex:
    a = cfg.radius
    v = cfg.metal_index
    ki, ke = _radial_wavenumbers(gamma, cfg)
    return (ki / ke) * (hankel1e(1, ke * a) / hankel1e(0, ke * a)) - jv(1, ki * a) / jv(0, ki * a)


def tm_equation(gamma: complex, cfg: WaveguideConfig) -> complex:
    a = cfg.radius
    v = cfg.metal_index
    ki, ke = _radial_wavenumbers(gamma, cfg)
    return v**2 * (ki / ke) * (hankel1e(1, ke * a) / hankel1e(0, ke * a)) * jv(0, ki * a) - jv(1, ki * a)


def bessel_seed(family: str, n: int, m: int) -> float:
    family = family.upper()
    if m < 1:
        raise ValueError("m must be >= 1")
    if family == "TE":
        if n != 0:
            raise ValueError("This reduced basis contains only TE_0m modes.")
        return float(jn_zeros(1, m)[-1])
    if family == "TM":
        if n != 0:
            raise ValueError("This reduced basis contains only TM_0m modes.")
        return float(jn_zeros(0, m)[-1])
    if family == "HE":
        if n < 1:
            raise ValueError("HE modes require n >= 1.")
        return float(jn_zeros(n - 1, m)[-1])
    if family == "EH":
        if n < 1:
            raise ValueError("EH modes require n >= 1.")
        return float(jn_zeros(n + 1, m)[-1])
    raise ValueError(f"Unknown mode family: {family}")


def _equation_for(family: str, n: int, cfg: WaveguideConfig):
    family = family.upper()
    if family == "TE":
        return lambda gamma: te_equation(gamma, cfg)
    if family == "TM":
        return lambda gamma: tm_equation(gamma, cfg)
    if family in {"HE", "EH"}:
        return lambda gamma: hybrid_equation(gamma, n, cfg)
    raise ValueError(f"Unknown mode family: {family}")


def _marcatili_amplitude_guess(family: str, u: float, cfg: WaveguideConfig) -> float:
    v = cfg.metal_index
    if family == "TE":
        nu = 1.0 / np.sqrt(v**2 - 1.0)
    elif family == "TM":
        nu = v**2 / np.sqrt(v**2 - 1.0)
    else:
        nu = (v**2 + 1.0) / (2.0 * np.sqrt(v**2 - 1.0))
    power_alpha = (u / (2.0 * np.pi)) ** 2 * cfg.wavelength**2 / cfg.radius**3 * np.real(nu)
    return max(float(power_alpha) * 0.5, 1e-12)


def _solve_tm_mode_scaled(n: int, m: int, cfg: WaveguideConfig, *, maxfev: int) -> Mode:
    """Solve TM_0m in transverse-u coordinates instead of ill-scaled beta/alpha."""

    if n != 0:
        raise ValueError("This reduced basis contains only TM_0m modes.")
    seeds = jn_zeros(0, m + 1)
    u_seed = float(seeds[m - 1])
    upper = float(seeds[m])
    k0 = cfg.k0
    radius = cfg.radius

    def system(values: np.ndarray) -> tuple[float, float]:
        u = values[0] + 1j * values[1]
        gamma = np.sqrt(k0**2 - (u / radius) ** 2 + 0j)
        value = tm_equation(gamma, cfg)
        return float(np.real(value)), float(np.imag(value))

    best_values: np.ndarray | None = None
    best_residual = np.inf
    for fraction in (0.15, 0.4, 0.7, 0.9):
        guess = np.array([u_seed + fraction * (upper - u_seed), -5e-4])
        result = least_squares(
            system,
            guess,
            bounds=([u_seed + 1e-9, -0.5], [upper - 1e-9, -1e-14]),
            xtol=1e-13,
            ftol=1e-13,
            gtol=1e-13,
            max_nfev=max(1000, 10 * int(maxfev)),
            x_scale="jac",
        )
        residual = float(np.linalg.norm(system(result.x)))
        if residual < best_residual:
            best_values = result.x
            best_residual = residual

    if best_values is None:
        alpha = _marcatili_amplitude_guess("TM", u_seed, cfg)
        beta = np.sqrt(max(0.0, k0**2 - (u_seed / radius) ** 2))
        return Mode("TM", n, m, u_seed, complex(beta, alpha), False, np.inf)

    solved_u = best_values[0] + 1j * best_values[1]
    gamma = complex(np.sqrt(k0**2 - (solved_u / radius) ** 2 + 0j))
    physical = gamma.real > 0.0 and gamma.imag >= 0.0 and gamma.real <= 1.000001 * k0
    converged = bool(physical and best_residual <= 1e-7)
    return Mode("TM", n, m, u_seed, gamma, converged, best_residual)


def solve_mode(
    family: str,
    n: int,
    m: int,
    cfg: WaveguideConfig,
    *,
    tol: float = 1e-11,
    maxfev: int = 200,
) -> Mode:
    family = family.upper()
    if family == "TM":
        return _solve_tm_mode_scaled(n, m, cfg, maxfev=maxfev)
    u0 = bessel_seed(family, n, m)
    k0 = cfg.k0
    a = cfg.radius
    beta0_sq = k0**2 - (u0 / a) ** 2
    beta0 = np.sqrt(beta0_sq) if beta0_sq > 0.0 else 0.999 * k0
    alpha0 = _marcatili_amplitude_guess(family, u0, cfg)
    equation = _equation_for(family, n, cfg)

    def real_system(x: np.ndarray) -> tuple[float, float]:
        value = equation(x[0] + 1j * x[1])
        return float(np.real(value)), float(np.imag(value))

    guesses = [
        np.array([beta0, alpha0]),
        np.array([beta0, 1e-9 * k0]),
        np.array([beta0 * (1.0 - 1e-10), alpha0]),
        np.array([beta0, 4e-3]),
    ]

    best = None
    best_residual = np.inf
    for guess in guesses:
        result = root(real_system, guess, tol=tol, options={"maxfev": maxfev})
        gamma = result.x[0] + 1j * result.x[1]
        residual = abs(equation(gamma))
        physical = isfinite(gamma.real) and isfinite(gamma.imag) and gamma.real > 0.0
        if gamma.real > 1.000001 * k0:
            physical = False
        if gamma.imag < -1e-10:
            physical = False
        if physical and residual < best_residual:
            best = result
            best_residual = float(residual)

    if best is None:
        return Mode(family, n, m, u0, complex(beta0, alpha0), False, np.inf)

    gamma = complex(best.x[0], abs(best.x[1]))
    converged = bool(best_residual <= 1e-6)
    return Mode(family, n, m, u0, gamma, converged, best_residual)


def solve_modes(
    cfg: WaveguideConfig,
    *,
    n_max: int = 4,
    m_max: int = 8,
    include_te_tm: bool = True,
) -> list[Mode]:
    modes: list[Mode] = []
    if include_te_tm:
        for family in ("TE", "TM"):
            for m in range(1, m_max + 1):
                modes.append(solve_mode(family, 0, m, cfg))

    for n in range(1, n_max + 1):
        for family in ("HE", "EH"):
            for m in range(1, m_max + 1):
                modes.append(solve_mode(family, n, m, cfg))

    return modes


def solve_mode_specs(
    cfg: WaveguideConfig,
    specs: list[ModeSpec],
    *,
    tol: float = 1e-11,
    maxfev: int = 200,
) -> list[Mode]:
    """Solve only explicitly requested modes."""

    return [
        solve_mode(spec.family, spec.n, spec.m, cfg, tol=tol, maxfev=maxfev)
        for spec in specs
    ]
