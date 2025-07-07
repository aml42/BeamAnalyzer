"""
Example usage of the BeamAnalyzer class - the main interface for beam analysis.

This example demonstrates all the features of the basic_mechanics package through
the unified BeamAnalyzer interface.
"""
import matplotlib.pyplot as plt
from src.loadcalculator.beam_analyzer import BeamAnalyzer
from src.loadcalculator.loads import UniformLoad, TriangularLoad


def example_single_span():
    """Example 1: Simple single span beam with uniform load."""
    print("=== Example 1: Single Span Beam ===")
    
    # Define the problem
    support_positions = [0.0, 5.0]  # 5m span
    loads = [UniformLoad(magnitude=1, start=0, end=5)]  # 10 kN/m = 10000 N/m uniform load
    
    # Create analyzer (without inertia - no deflection calculation)
    analyzer = BeamAnalyzer(
        support_positions=support_positions,
        loads=loads,
        inertia=138
    )
    
    # Perform analysis
    results = analyzer.analyze()
    
    # Print results
    print(f"Reactions: {results['reactions']}")
    print(f"Moments at supports: {results['moments_at_supports']}")
    print(f"Max moments per span: {results['max_moments_per_span']}")
    print(f"Max shear per span: {results['max_shear_per_span']}")
    print(f"Max deflection per span: {results['max_deflection_per_span']}")
    
    # Plot diagrams
    fig, (ax1, ax2, ax3) = analyzer.plot_all_diagrams()
    plt.show()


def example_continuous_beam():
    """Example 2: Continuous beam with multiple loads."""
    print("\n=== Example 2: Continuous Beam ===")
    
    # Define the problem
    support_positions = [0.0, 4.0, 8.0, 12.0]  # 3 spans: 4m, 4m, 4m
    loads = [
        UniformLoad(magnitude=15, start=0, end=4),      # 15 kN/m = 15000 N/m on first span
        TriangularLoad(magnitude_start=0, magnitude_end=20, start=4, end=8),  # 20 kN/m = 20000 N/m triangular load on second span
        UniformLoad(magnitude=10, start=8, end=12)      # 10 kN/m = 10000 N/m on third span
    ]
    
    # Create analyzer with deflection calculation
    analyzer = BeamAnalyzer(
        support_positions=support_positions,
        loads=loads,
        inertia=138,  # 138 cm⁴
        e_modulus=210000  # 210 MPa (steel)
    )
    
    # Perform analysis
    results = analyzer.analyze()
    
    # Print results
    print(f"Reactions: {results['reactions']}")
    print(f"Moments at supports: {results['moments_at_supports']}")
    print(f"Max moments per span: {results['max_moments_per_span']}")
    print(f"Max shear per span: {results['max_shear_per_span']}")
    print(f"Max deflection per span: {results['max_deflection_per_span']}")
    
    # Plot all diagrams
    fig, (ax1, ax2, ax3) = analyzer.plot_all_diagrams()
    plt.show()


def example_get_values():
    """Example 3: Getting specific values and data arrays."""
    print("\n=== Example 3: Getting Specific Values ===")
    
    # Define the problem
    support_positions = [0.0, 5.0]
    loads = [UniformLoad(magnitude=1, start=0, end=6)]  # 12 kN/m = 12000 N/m
    
    analyzer = BeamAnalyzer(
        support_positions=support_positions,
        loads=loads,
        inertia=138
    )
    
    # Get values at specific positions
    positions = [1.0, 3.0, 5.0]
    for pos in positions:
        values = analyzer.get_value_at_position(pos)
        print(f"At x = {pos}m:")
        print(f"  Shear: {values['shear']:.2f} N")
        print(f"  Moment: {values['moment']:.2f} Nm")
        print(f"  Deflection: {values['deflection']:.4f} mm")
    
    # Get all values for plotting
    x_coords, shear_values = analyzer.get_shear_values()
    _, moment_values = analyzer.get_moment_values()
    _, deflection_values = analyzer.get_deflection_values()
    
    print(f"\nNumber of calculation points: {len(x_coords)}")
    print(f"Shear range: {shear_values.min():.2f} to {shear_values.max():.2f} N")
    print(f"Moment range: {moment_values.min():.2f} to {moment_values.max():.2f} Nm")
    print(f"Deflection range: {deflection_values.min():.4f} to {deflection_values.max():.4f} mm")


def example_save_plots():
    """Example 4: Saving plots to files."""
    print("\n=== Example 4: Saving Plots ===")
    
    # Define the problem
    support_positions = [0.0, 3.0, 7.0]
    loads = [
        UniformLoad(magnitude=8, start=0, end=3),  # 8 kN/m
        TriangularLoad(magnitude_start=0, magnitude_end=16, start=3, end=7)  # 16 kN/m
    ]
    
    analyzer = BeamAnalyzer(
        support_positions=support_positions,
        loads=loads,
        inertia=138
    )
    
    # Save individual diagrams
    analyzer.plot_shear_diagram(save_path="shear_diagram.png")
    analyzer.plot_moment_diagram(save_path="moment_diagram.png")
    analyzer.plot_deflection_diagram(save_path="deflection_diagram.png")
    
    # Save combined diagram
    analyzer.plot_all_diagrams(save_path="all_diagrams.png")
    
    print("Plots saved as:")
    print("- shear_diagram.png")
    print("- moment_diagram.png") 
    print("- deflection_diagram.png")
    print("- all_diagrams.png")


def example_complex_loading():
    """Example 5: Complex loading scenario."""
    print("\n=== Example 5: Complex Loading ===")
    
    # Define a complex beam with multiple spans and loads
    support_positions = [0.0, 2.5, 5.0, 8.0, 11.0]  # 4 spans
    loads = [
        UniformLoad(magnitude=20, start=0, end=2.5),           # 20 kN/m on first span
        TriangularLoad(magnitude_start=0, magnitude_end=30, start=2.5, end=5),  # 30 kN/m triangular on second span
        UniformLoad(magnitude=15, start=5, end=8),             # 15 kN/m on third span
        TriangularLoad(magnitude_start=25, magnitude_end=0, start=8, end=11)    # 25 kN/m decreasing triangular on fourth span
    ]
    
    analyzer = BeamAnalyzer(
        support_positions=support_positions,
        loads=loads,
        inertia=138,
        e_modulus=210000
    )
    
    # Perform analysis
    results = analyzer.analyze()
    
    # Print detailed results
    print("Support Reactions:")
    for pos, reaction in results['reactions'].items():
        print(f"  Support at {pos}m: {reaction:.2f} N")
    
    print("\nMoments at Supports:")
    for pos, moment in results['moments_at_supports'].items():
        print(f"  Moment at {pos}m: {moment:.2f} Nm")
    
    print("\nMaximum Values per Span:")
    for i, (moment_info, shear_info) in enumerate(zip(results['max_moments_per_span'], results['max_shear_per_span'])):
        print(f"  Span {i+1} ({moment_info['span_start']:.1f}m - {moment_info['span_end']:.1f}m):")
        print(f"    Max moment: {moment_info['max_moment']:.2f} Nm at {moment_info['max_moment_position']:.2f}m")
        print(f"    Max shear: {shear_info['max_shear']:.2f} N at {shear_info['max_shear_position']:.2f}m")
    
    if 'max_deflection_per_span' in results:
        print("\nMaximum Deflections per Span:")
        for i, deflection_info in enumerate(results['max_deflection_per_span']):
            print(f"  Span {i+1}: {deflection_info['max_deflection']:.4f} mm at {deflection_info['max_deflection_position']:.2f}m")
    
    # Plot and show
    analyzer.plot_all_diagrams()
    plt.show()


if __name__ == "__main__":
    # Run all examples
    example_single_span()
    example_continuous_beam()
    example_get_values()
    # example_save_plots()
    example_complex_loading()