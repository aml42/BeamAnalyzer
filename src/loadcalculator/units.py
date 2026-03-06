from enum import Enum


# ---------------------------------------------------------------------------
# Output units (multiply SI value by .scale to get display value)
# ---------------------------------------------------------------------------

class ShearUnit(Enum):
    """Unit for shear force output."""
    N = (1.0, "N")
    kN = (1e-3, "kN")

    def __init__(self, scale: float, label: str):
        self.scale = scale
        self.label = label


class MomentUnit(Enum):
    """Unit for bending moment output."""
    Nm = (1.0, "N·m")
    kNm = (1e-3, "kN·m")
    Nmm = (1e3, "N·mm")

    def __init__(self, scale: float, label: str):
        self.scale = scale
        self.label = label


class DeflectionUnit(Enum):
    """Unit for deflection output."""
    m = (1.0, "m")
    dm = (10.0, "dm")
    cm = (100.0, "cm")
    mm = (1000.0, "mm")

    def __init__(self, scale: float, label: str):
        self.scale = scale
        self.label = label


# ---------------------------------------------------------------------------
# Input units (multiply input value by .to_si to convert to SI)
# ---------------------------------------------------------------------------

class LengthUnit(Enum):
    """Unit for positions / lengths. Multiply value by .to_si to get metres."""
    m = (1.0, "m")
    dm = (1e-1, "dm")
    cm = (1e-2, "cm")
    mm = (1e-3, "mm")

    def __init__(self, to_si: float, label: str):
        self.to_si = to_si
        self.label = label


class ForcePerLengthUnit(Enum):
    """Unit for distributed-load magnitudes. Multiply value by .to_si to get N/m."""
    N_per_m = (1.0, "N/m")
    kN_per_m = (1e3, "kN/m")
    N_per_mm = (1e3, "N/mm")

    def __init__(self, to_si: float, label: str):
        self.to_si = to_si
        self.label = label


class PressureUnit(Enum):
    """Unit for elastic modulus / pressure. Multiply value by .to_si to get Pa."""
    Pa = (1.0, "Pa")
    kPa = (1e3, "kPa")
    MPa = (1e6, "MPa")
    GPa = (1e9, "GPa")

    def __init__(self, to_si: float, label: str):
        self.to_si = to_si
        self.label = label


class InertiaUnit(Enum):
    """Unit for second moment of area. Multiply value by .to_si to get m⁴."""
    m4 = (1.0, "m⁴")
    dm4 = (1e-4, "dm⁴")
    cm4 = (1e-8, "cm⁴")
    mm4 = (1e-12, "mm⁴")

    def __init__(self, to_si: float, label: str):
        self.to_si = to_si
        self.label = label
