# BeamAnalyzer - Continuous Beam Analysis

The `BeamAnalyzer` class provides a unified interface for analyzing continuous beams. It calculates support reactions, shear forces, bending moments, and deflections using the three-moment equation (Clapeyron's theorem).

## Quick Start

```python
from loadcalculator import BeamAnalyzer, UniformLoad, TriangularLoad

analyzer = BeamAnalyzer(
    support_positions=[0.0, 4.0, 8.0],
    loads=[
        UniformLoad(magnitude=10000, start=0, end=4),
        TriangularLoad(magnitude_start=0, magnitude_end=20000, start=4, end=8),
    ],
    inertia=138e-8,       # m⁴ (for deflection calculation)
    e_modulus=2.1e11,     # Pa (steel)
)

results = analyzer.analyze()
print(results['reactions'])
print(results['max_moments_per_span'])
```

## Installation

```bash
uv sync
```

## Input Parameters

### Required

| Parameter | Description |
|---|---|
| `support_positions` | Support positions along the beam axis |
| `loads` | List of `UniformLoad` and/or `TriangularLoad` objects |

### Optional

| Parameter | Default | Description |
|---|---|---|
| `inertia` | `None` | Moment of inertia. If `None`, deflection is skipped |
| `e_modulus` | `2.1e11` | Elastic modulus (default: steel in Pa) |
| `num_points` | `2000` | Number of evaluation points |

### Input Units

By default all inputs are in SI (m, N/m, Pa, m⁴). You can change this with input unit enums:

| Parameter | Default | Options |
|---|---|---|
| `position_unit` | `LengthUnit.m` | `m`, `dm`, `cm`, `mm` |
| `load_unit` | `ForcePerLengthUnit.N_per_m` | `N_per_m`, `kN_per_m`, `N_per_mm` |
| `e_modulus_unit` | `PressureUnit.Pa` | `Pa`, `kPa`, `MPa`, `GPa` |
| `inertia_unit` | `InertiaUnit.m4` | `m4`, `dm4`, `cm4`, `mm4` |

All inputs are converted to SI internally before computation.

```python
from loadcalculator import (
    BeamAnalyzer, UniformLoad,
    LengthUnit, ForcePerLengthUnit, PressureUnit, InertiaUnit,
)

analyzer = BeamAnalyzer(
    support_positions=[0, 3000, 6000, 9000, 12000],
    loads=[UniformLoad(magnitude=19.575, start=0, end=12000)],
    inertia=3265,
    e_modulus=210000,
    position_unit=LengthUnit.mm,
    load_unit=ForcePerLengthUnit.kN_per_m,
    e_modulus_unit=PressureUnit.MPa,
    inertia_unit=InertiaUnit.cm4,
)
```

### Output Units

Output units for results and plots are also configurable:

| Parameter | Default | Options |
|---|---|---|
| `shear_unit` | `ShearUnit.N` | `N`, `kN` |
| `moment_unit` | `MomentUnit.Nm` | `Nm`, `kNm`, `Nmm` |
| `deflection_unit` | `DeflectionUnit.m` | `m`, `dm`, `cm`, `mm` |

These affect `analyze()` results, `get_value_at_position()`, data retrieval methods, and plot axis labels.

```python
from loadcalculator import BeamAnalyzer, UniformLoad, ShearUnit, MomentUnit, DeflectionUnit

analyzer = BeamAnalyzer(
    support_positions=[0.0, 3.0, 6.0],
    loads=[UniformLoad(magnitude=10000, start=0, end=6)],
    inertia=138e-8,
    shear_unit=ShearUnit.kN,
    moment_unit=MomentUnit.kNm,
    deflection_unit=DeflectionUnit.mm,
)

results = analyzer.analyze()
# results['reactions'] in kN, moments in kN·m, deflections in mm
```

## Output Structure

`analyze()` returns a dictionary:

```python
{
    'reactions': {0.0: 25.0, 4.0: 50.0, 8.0: 25.0},
    'moments_at_supports': {0.0: 0.0, 4.0: -20000.0, 8.0: 0.0},
    'max_moments_per_span': [
        {'span_index': 0, 'span_start': 0.0, 'span_end': 4.0,
         'max_moment': 20000.0, 'max_moment_position': 2.0},
        ...
    ],
    'max_shear_per_span': [
        {'span_index': 0, 'span_start': 0.0, 'span_end': 4.0,
         'max_shear': 15000.0, 'max_shear_position': 0.0},
        ...
    ],
    'max_deflection_per_span': [  # only if inertia is provided
        {'span_index': 0, 'span_start': 0.0, 'span_end': 4.0,
         'max_deflection': -0.0123, 'max_deflection_position': 2.0},
        ...
    ],
}
```

## Methods

### Analysis

- **`analyze()`** — Full analysis, returns results dict
- **`get_value_at_position(position)`** — Shear, moment, and deflection at a specific position

### Data Retrieval

- **`get_shear_values()`** — `(x_array, shear_array)`
- **`get_moment_values()`** — `(x_array, moment_array)`
- **`get_deflection_values()`** — `(x_array, deflection_array)` (requires inertia)

### Plotting

All plot methods accept an optional `unit` parameter to override the analyzer default.

- **`plot_shear_diagram(save_path=None, unit=None)`**
- **`plot_moment_diagram(save_path=None, unit=None)`**
- **`plot_deflection_diagram(save_path=None, unit=None)`** (requires inertia)
- **`plot_all_diagrams(save_path=None, figsize=(15, 10), shear_unit=None, moment_unit=None, deflection_unit=None)`** — Moment, shear, and deflection in one figure

## Load Types

### UniformLoad

```python
UniformLoad(magnitude=10000, start=0, end=5)
```

- `magnitude` — load intensity (in `load_unit`)
- `start` / `end` — position range (in `position_unit`)

### TriangularLoad

```python
TriangularLoad(magnitude_start=0, magnitude_end=20000, start=0, end=5)
```

- `magnitude_start` / `magnitude_end` — load intensity at start/end (in `load_unit`)
- `start` / `end` — position range (in `position_unit`)

## Running Tests

```bash
uv run pytest
uv run pytest tests/beam_analyzer_test.py -v  # single file
```

## Notes

- Deflection is only calculated when `inertia` is provided
- End supports always have zero moment (simply supported)
- Positive shear is upward; negative deflection is downward
- Analysis is computed once and cached — subsequent calls reuse results
