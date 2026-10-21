from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.special import jv

from .config import BeamConfig, WaveguideConfig
from .cylindrical_modes import Mode


@dataclass(frozen=True)
class Grid:
    x: np.ndarray
    y: np.ndarray
    X: np.ndarray
    Y: np.ndarray
    R: np.ndarray
    Phi: np.ndarray
    core_mask: np.ndarray
    area_element: float


@dataclass
class Field2D:
    Ex: np.ndarray
    Ey: np.ndarray


@dataclass
class ModeProfile:
    mode: Mode
    orientation: str
    Ex: np.ndarray
    Ey: np.ndarray
    norm: float

    @property
    def name(self) -> str:
        return self.mode.name if self.orientation == "" else f"{self.mode.name}{self.orientation}"


@dataclass
class DecompositionResult:
    grid: Grid
    input_field: Field2D
    profiles: list[ModeProfile]
    coefficients: np.ndarray
    input_power: float
    coupled_power: float
    residual_power: float
    singular_values: np.ndarray

    def propagated_field(self, z: float) -> Field2D:
        Ex = np.zeros_like(self.input_field.Ex, dtype=complex)
        Ey = np.zeros_like(self.input_field.Ey, dtype=complex)
        for coeff, profile in zip(self.coefficients, self.profiles):
            phase = np.exp(1j * profile.mode.gamma * z)
            Ex += coeff * profile.Ex * phase
            Ey += coeff * profile.Ey * phase
        return Field2D(Ex=Ex, Ey=Ey)

    def power_at(self, z: float) -> float:
        field = self.propagated_field(z)
        return field_power(field, self.grid)


def make_grid(radius: float, samples: int = 160, margin: float = 1.0) -> Grid:
    span = margin * radius
    x = np.linspace(-span, span, samples)
    y = np.linspace(-span, span, samples)
    X, Y = np.meshgrid(x, y)
    R = np.sqrt(X**2 + Y**2)
    Phi = np.arctan2(Y, X)
    core_mask = R <= radius
    area_element = float((x[1] - x[0]) * (y[1] - y[0]))
    return Grid(x=x, y=y, X=X, Y=Y, R=R, Phi=Phi, core_mask=core_mask, area_element=area_element)


def gaussian_beam_field(grid: Grid, waveguide: WaveguideConfig, beam: BeamConfig) -> Field2D:
    waist = beam.resolved_waist(waveguide)
    phase = waveguide.k0 * (np.sin(beam.tilt_x) * grid.X + np.sin(beam.tilt_y) * grid.Y)
    envelope = np.exp(-((grid.X - beam.offset_x) ** 2 + (grid.Y - beam.offset_y) ** 2) / waist**2)
    scalar = envelope * np.exp(1j * phase)
    Ex = np.zeros_like(grid.X, dtype=complex)
    Ey = np.zeros_like(grid.Y, dtype=complex)
    Ex[grid.core_mask] = beam.polarization_x * scalar[grid.core_mask]
    Ey[grid.core_mask] = beam.polarization_y * scalar[grid.core_mask]
    return Field2D(Ex=Ex, Ey=Ey)


def field_power(field: Field2D, grid: Grid) -> float:
    density = np.abs(field.Ex) ** 2 + np.abs(field.Ey) ** 2
    return float(np.sum(density[grid.core_mask]) * grid.area_element)


def _profile_components(mode: Mode, grid: Grid, radius: float, orientation: str) -> Field2D:
    family = mode.family.upper()
    Ex = np.zeros_like(grid.X, dtype=complex)
    Ey = np.zeros_like(grid.Y, dtype=complex)
    rho = grid.R[grid.core_mask] / radius
    phi = grid.Phi[grid.core_mask]

    if family == "TE":
        radial = jv(1, mode.u_seed * rho)
        Ex[grid.core_mask] = -radial * np.sin(phi)
        Ey[grid.core_mask] = radial * np.cos(phi)
    elif family == "TM":
        radial = jv(1, mode.u_seed * rho)
        Ex[grid.core_mask] = radial * np.cos(phi)
        Ey[grid.core_mask] = radial * np.sin(phi)
    elif family == "HE":
        q = mode.n - 1
        radial = jv(q, mode.u_seed * rho)
        if orientation == "s":
            Ex[grid.core_mask] = radial * np.sin(q * phi)
            Ey[grid.core_mask] = radial * np.cos(q * phi)
        else:
            Ex[grid.core_mask] = radial * np.cos(q * phi)
            Ey[grid.core_mask] = -radial * np.sin(q * phi)
    elif family == "EH":
        q = mode.n + 1
        radial = jv(q, mode.u_seed * rho)
        if orientation == "s":
            Ex[grid.core_mask] = radial * np.sin(q * phi)
            Ey[grid.core_mask] = -radial * np.cos(q * phi)
        else:
            Ex[grid.core_mask] = radial * np.cos(q * phi)
            Ey[grid.core_mask] = radial * np.sin(q * phi)
    else:
        raise ValueError(f"Unknown mode family: {mode.family}")

    return Field2D(Ex=Ex, Ey=Ey)


def build_profiles(modes: list[Mode], grid: Grid, waveguide: WaveguideConfig) -> list[ModeProfile]:
    profiles: list[ModeProfile] = []
    for mode in modes:
        if not mode.converged:
            continue
        orientations = ("",) if mode.family in {"TE", "TM"} else ("c", "s")
        for orientation in orientations:
            field = _profile_components(mode, grid, waveguide.radius, orientation)
            norm = np.sqrt(field_power(field, grid))
            if norm <= 0.0:
                continue
            profiles.append(
                ModeProfile(
                    mode=mode,
                    orientation=orientation,
                    Ex=field.Ex / norm,
                    Ey=field.Ey / norm,
                    norm=float(norm),
                )
            )
    return profiles


def _weighted_flatten(field: Field2D, grid: Grid) -> np.ndarray:
    scale = np.sqrt(grid.area_element)
    return np.concatenate(
        [
            field.Ex[grid.core_mask].ravel() * scale,
            field.Ey[grid.core_mask].ravel() * scale,
        ]
    )


def decompose_field(
    input_field: Field2D,
    profiles: list[ModeProfile],
    grid: Grid,
    *,
    rcond: float = 1e-9,
) -> DecompositionResult:
    if not profiles:
        raise ValueError("No mode profiles were provided.")

    y = _weighted_flatten(input_field, grid)
    matrix = np.column_stack([_weighted_flatten(Field2D(p.Ex, p.Ey), grid) for p in profiles])
    coeffs, _, _, singular_values = np.linalg.lstsq(matrix, y, rcond=rcond)
    y_fit = matrix @ coeffs
    input_power = float(np.vdot(y, y).real)
    coupled_power = float(np.vdot(y_fit, y_fit).real)
    residual_power = max(0.0, input_power - coupled_power)
    return DecompositionResult(
        grid=grid,
        input_field=input_field,
        profiles=profiles,
        coefficients=coeffs,
        input_power=input_power,
        coupled_power=coupled_power,
        residual_power=residual_power,
        singular_values=singular_values,
    )


def decompose_gaussian(
    modes: list[Mode],
    waveguide: WaveguideConfig,
    beam: BeamConfig,
    *,
    samples: int = 160,
    rcond: float = 1e-9,
) -> DecompositionResult:
    grid = make_grid(waveguide.radius, samples=samples)
    field = gaussian_beam_field(grid, waveguide, beam)
    profiles = build_profiles(modes, grid, waveguide)
    return decompose_field(field, profiles, grid, rcond=rcond)
