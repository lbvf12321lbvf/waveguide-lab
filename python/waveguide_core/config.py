from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WaveguideConfig:
    """Physical parameters of a circular hollow metallic waveguide."""

    wavelength: float = 800e-9
    diameter: float = 300e-6
    metal_epsilon: complex = -31.021 + 0.40948j
    roughness_rms: float = 0.0

    @property
    def radius(self) -> float:
        return 0.5 * self.diameter

    @property
    def k0(self) -> float:
        import numpy as np

        return 2.0 * np.pi / self.wavelength

    @property
    def metal_index(self) -> complex:
        import numpy as np

        return complex(np.sqrt(self.metal_epsilon))


@dataclass(frozen=True)
class BeamConfig:
    """Input Gaussian beam parameters in SI units."""

    waist: float | None = None
    offset_x: float = 0.0
    offset_y: float = 0.0
    tilt_x: float = 0.0
    tilt_y: float = 0.0
    polarization_x: complex = 1.0 + 0.0j
    polarization_y: complex = 0.0 + 0.0j

    def resolved_waist(self, waveguide: WaveguideConfig) -> float:
        if self.waist is not None:
            return self.waist
        return 0.3 * waveguide.radius
