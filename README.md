# BeamAnalyzer - Main Interface for Beam Analysis

The `BeamAnalyzer` class provides a unified interface for analyzing continuous beams with the `basic_mechanics` package. It combines all the functionality into a single, easy-to-use class that uses SI units throughout.

## Quick Start

```python
from loadcalculator import BeamAnalyzer, UniformLoad, TriangularLoad

# Define your beam
support_positions = [0.0, 4.0, 8.0]  # Two spans: 4m each
loads = [
    UniformLoad(magnitude=10000, start=0, end=4),      # 10 kN/m = 10000 N/m on first span
    TriangularLoad(magnitude_start=0, magnitude_end=20000, start=4, end=8)  # 20 kN/m = 20000 N/m triangular on second span
]

# Create analyzer
analyzer = BeamAnalyzer(
    support_positions=support_positions,
    loads=loads,
    inertia=1000,  # Optional: for deflection calculation
    e_modulus=210000  # Optional: default is steel
)

# Perform analysis
results = analyzer.analyze()

# Access results
print(f"Reactions: {results['reactions']}")
print(f"Max moments: {results['max_moments_per_span']}")
```

## Input Parameters

### Required Parameters

- **`support_positions`** (List[float]): List of support positions along the beam axis in meters
- **`loads`** (List[UniformLoad | TriangularLoad]): List of load objects with magnitudes in N/m

### Optional Parameters

- **`inertia`** (float, optional): Moment of inertia in cm⁴. If not provided, deflection calculations are skipped
- **`e_modulus`** (float, default=210000): Elastic modulus in N/mm² (default is typical for steel)
- **`num_points`** (int, default=2000): Number of evaluation points for calculations and plotting

## Output Structure

The `analyze()` method returns a dictionary containing:

```python
{
    'reactions': {support_position: reaction_force},
    'moments_at_supports': {support_position: moment_value},
    'max_moments_per_span': [
        {
            'span_index': 0,
            'span_start': 0.0,
            'span_end': 4.0,
            'max_moment': 20000.0,
            'max_moment_position': 2.0
        },
        # ... one entry per span
    ],
    'max_shear_per_span': [
        {
            'span_index': 0,
            'span_start': 0.0,
            'span_end': 4.0,
            'max_shear': 15000.0,
            'max_shear_position': 0.0
        },
        # ... one entry per span
    ],
    'max_deflection_per_span': [  # Only if inertia is provided
        {
            'span_index': 0,
            'span_start': 0.0,
            'span_end': 4.0,
            'max_deflection': 0.0123,
            'max_deflection_position': 2.0
        },
        # ... one entry per span
    ]
}
```

## Available Methods

### Analysis Methods

- **`analyze()`**: Perform complete beam analysis and return all results
- **`get_value_at_position(position)`**: Get shear, moment, and deflection at a specific position

### Data Retrieval Methods

- **`get_shear_values()`**: Returns (x_coordinates, shear_values) arrays
- **`get_moment_values()`**: Returns (x_coordinates, moment_values) arrays
- **`get_deflection_values()`**: Returns (x_coordinates, deflection_values) arrays (requires inertia)

### Plotting Methods

- **`plot_shear_diagram(save_path=None, **kwargs)`**: Plot shear force diagram
- **`plot_moment_diagram(save_path=None, **kwargs)`**: Plot bending moment diagram
- **`plot_deflection_diagram(save_path=None, **kwargs)`**: Plot deflection diagram (requires inertia)
- **`plot_all_diagrams(save_path=None, figsize=(15, 10))`**: Plot all diagrams in one figure

## Load Types

### UniformLoad

```python
UniformLoad(magnitude=10000, start=0, end=5)  # 10 kN/m = 10000 N/m
```

- **`magnitude`**: Load intensity in N/m
- **`start`**: Start position of the load in meters
- **`end`**: End position of the load in meters

### TriangularLoad

```python
TriangularLoad(magnitude_start=0, magnitude_end=20000, start=0, end=5)  # 20 kN/m = 20000 N/m
```

- **`magnitude_start`**: Load intensity at start position in N/m
- **`magnitude_end`**: Load intensity at end position in N/m
- **`start`**: Start position of the load in meters
- **`end`**: End position of the load in meters

## Examples

### Example 1: Simple Single Span

```python
from loadcalculator import BeamAnalyzer, UniformLoad

# Simple beam with uniform load
analyzer = BeamAnalyzer(
    support_positions=[0.0, 5.0],
    loads=[UniformLoad(magnitude=10000, start=0, end=5)]  # 10 kN/m = 10000 N/m
)

results = analyzer.analyze()
print(f"Reactions: {results['reactions']}")

# Plot diagrams
analyzer.plot_all_diagrams()
plt.show()
```

### Example 2: Continuous Beam with Deflection

```python
from loadcalculator import BeamAnalyzer, UniformLoad, TriangularLoad

# Continuous beam with multiple loads
analyzer = BeamAnalyzer(
    support_positions=[0.0, 4.0, 8.0, 12.0],
    loads=[
        UniformLoad(magnitude=15000, start=0, end=4),      # 15 kN/m = 15000 N/m
        TriangularLoad(magnitude_start=0, magnitude_end=20000, start=4, end=8),  # 20 kN/m = 20000 N/m
        UniformLoad(magnitude=10000, start=8, end=12)      # 10 kN/m = 10000 N/m
    ],
    inertia=1000,  # Enable deflection calculation
    e_modulus=210000
)

results = analyzer.analyze()

# Get values at specific position
values = analyzer.get_value_at_position(6.0)
print(f"At x=6m: Shear={values['shear']:.2f} N, Moment={values['moment']:.2f} Nm")

# Save plots
analyzer.plot_all_diagrams(save_path="beam_analysis.png")
```

### Example 3: Getting Data Arrays

```python
# Get all values for custom plotting
x_coords, shear_values = analyzer.get_shear_values()
_, moment_values = analyzer.get_moment_values()
_, deflection_values = analyzer.get_deflection_values()

# Custom plotting
plt.figure(figsize=(15, 5))
plt.subplot(1, 3, 1)
plt.plot(x_coords, shear_values)
plt.title('Shear Force')
plt.grid(True)

plt.subplot(1, 3, 2)
plt.plot(x_coords, moment_values)
plt.title('Bending Moment')
plt.grid(True)

plt.subplot(1, 3, 3)
plt.plot(x_coords, deflection_values)
plt.title('Deflection')
plt.grid(True)

plt.tight_layout()
plt.show()
```

## Units

- **Positions**: meters (m)
- **Loads**: newtons per meter (N/m)
- **Reactions**: newtons (N)
- **Moments**: newton-meters (Nm)
- **Inertia**: centimeters to the fourth power (cm⁴)
- **E-modulus**: newtons per square millimeter (N/mm²)
- **Deflection**: millimeters (mm)

## Notes

1. **Deflection Calculation**: Deflection is only calculated if the `inertia` parameter is provided
2. **Support Moments**: End supports always have zero moment (simply supported)
3. **Coordinate System**: Positive shear is upward, positive moment causes tension on the bottom fiber
4. **Deflection Sign**: Positive deflection is downward (following load direction)
5. **SI Units**: All inputs use SI units, with internal conversions handled automatically for deflection calculations

## Error Handling

The analyzer will raise appropriate errors for:
- Insufficient support positions (< 2)
- No loads provided
- Invalid load parameters
- Missing inertia when deflection methods are called
- Numerical issues in solving the system

## Performance

- Analysis is performed once and cached for subsequent method calls
- Plotting methods reuse the cached analysis results
- Large numbers of evaluation points may slow down initial analysis but improve plot quality
