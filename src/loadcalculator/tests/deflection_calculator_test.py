import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loadcalculator.loads import UniformLoad, TriangularLoad
from loadcalculator.supports import Support
from loadcalculator.systembuilder import SystemBuilder
from loadcalculator.systemsolver import SystemSolver
from loadcalculator.reactionsolver import ReactionSolver
from loadcalculator.plotter import BeamPlotter
from loadcalculator.deflection_calculator import DeflectionCalculator
import matplotlib.pyplot as plt
import pytest

def test_deflection_calculator():
    """Test deflection calculation for a simple supported beam with uniform load.

    Uses a 4 m span (4000 mm) so deflection is measurable. With L=4 mm, deflection
    would be ~1.6e-8 mm (L^4 scaling). For w=10 N/mm, E=210000, I=16000 cm^4:
    delta_max = 5*w*L^4/(384*E*I) ≈ 1.0 mm at mid-span.
    """
    loads = [UniformLoad(10000, 0, 4)]  # 10 N/m over 4 m span
    supports = [Support(0), Support(4)]
    builder = SystemBuilder(loads, supports)
    solver = SystemSolver(builder)
    reaction_solver = ReactionSolver(builder, solver)
    plotter = BeamPlotter(builder, solver, reaction_solver)
    deflection_calc = DeflectionCalculator(plotter, e_modulus=210000, inertia=1)
    max_deflection, max_pos = deflection_calc.get_max_deflection()
    assert max_deflection == pytest.approx(-2.0, abs=0.1)  # downward = negative
    assert max_pos == pytest.approx(2000.0, abs=50.0)  # mid-span at 2000 mm

def test_simple_beam_deflection():
    """Test deflection calculation for a simple supported beam with uniform load."""
    print("=== Simple Beam Deflection Test ===")
    
    # Create a simple beam with uniform load
    loads = [UniformLoad(10, 0, 20)]  # 10 N/mm from 0 to 20 mm
    supports = [Support(0), Support(20)]  # Simply supported beam
    
    # Build and solve the system
    builder = SystemBuilder(loads, supports)
    solver = SystemSolver(builder)
    reaction_solver = ReactionSolver(builder, solver)
    plotter = BeamPlotter(builder, solver, reaction_solver)
    
    # Calculate deflection (example with I = 1000 cm⁴)
    deflection_calc = DeflectionCalculator(plotter, e_modulus=210000, inertia=1000)
    
    # Get maximum deflection
    max_deflection, max_pos = deflection_calc.get_max_deflection()
    print(f"Maximum deflection: {max_deflection:.6f} mm at position {max_pos:.1f} mm")
    
    # Get deflection at specific positions
    mid_deflection = deflection_calc.get_deflection_at_position(10)
    print(f"Deflection at mid-span (10 mm): {mid_deflection:.6f} mm")
    
    # Get slope at specific positions
    mid_slope = deflection_calc.get_slope_at_position(10)
    print(f"Slope at mid-span (10 mm): {mid_slope:.6f} rad")
    
    # Plot results
    fig, (ax1, ax2) = deflection_calc.plot_all()
    plt.suptitle("Simple Beam Deflection Analysis")
    plt.show()
    
    return deflection_calc


def test_continuous_beam_deflection():
    """Test deflection calculation for a continuous beam with multiple loads."""
    print("\n=== Continuous Beam Deflection Test ===")
    
    # Create a continuous beam with multiple loads
    loads = [
        UniformLoad(8, 0, 10),      # 8 N/mm from 0 to 10 mm
        TriangularLoad(0, 12, 10, 20),  # Triangular load from 10 to 20 mm
        UniformLoad(6, 20, 30)      # 6 N/mm from 20 to 30 mm
    ]
    supports = [Support(0), Support(15), Support(30)]  # Three supports
    
    # Build and solve the system
    builder = SystemBuilder(loads, supports)
    solver = SystemSolver(builder)
    reaction_solver = ReactionSolver(builder, solver)
    plotter = BeamPlotter(builder, solver, reaction_solver)
    
    # Calculate deflection (example with I = 2000 cm⁴)
    deflection_calc = DeflectionCalculator(plotter, e_modulus=210000, inertia=2000)
    
    # Get maximum deflection
    max_deflection, max_pos = deflection_calc.get_max_deflection()
    print(f"Maximum deflection: {max_deflection:.6f} mm at position {max_pos:.1f} mm")
    
    # Get deflection at support positions (should be close to zero)
    for i, support_pos in enumerate(plotter.support_positions):
        deflection = deflection_calc.get_deflection_at_position(support_pos)
        print(f"Deflection at support {i+1} ({support_pos} mm): {deflection:.6f} mm")
    
    # Plot results
    fig, (ax1, ax2) = deflection_calc.plot_all()
    plt.suptitle("Continuous Beam Deflection Analysis")
    plt.show()
    
    return deflection_calc


def test_comprehensive_analysis():
    """Test comprehensive analysis with all diagrams."""
    print("\n=== Comprehensive Analysis Test ===")
    
    # Create a complex beam system
    loads = [
        UniformLoad(15, 0, 8),      # 15 N/mm from 0 to 8 mm
        TriangularLoad(0, 20, 8, 16),  # Triangular load from 8 to 16 mm
        UniformLoad(10, 16, 24)     # 10 N/mm from 16 to 24 mm
    ]
    supports = [Support(0), Support(12), Support(24)]  # Three supports
    
    # Build and solve the system
    builder = SystemBuilder(loads, supports)
    solver = SystemSolver(builder)
    reaction_solver = ReactionSolver(builder, solver)
    plotter = BeamPlotter(builder, solver, reaction_solver)
    
    # Calculate deflection
    deflection_calc = DeflectionCalculator(plotter, e_modulus=210000, inertia=1500)
    
    # Create comprehensive plot with all diagrams
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    
    # Plot shear force
    plotter.plot_shear(ax1)
    ax1.set_title("Shear Force Diagram")
    
    # Plot bending moment
    plotter.plot_moment(ax2)
    ax2.set_title("Bending Moment Diagram")
    
    # Plot deflection
    deflection_calc.plot_deflection(ax3)
    ax3.set_title("Deflection Diagram")
    
    # Plot slope
    deflection_calc.plot_slope(ax4)
    ax4.set_title("Slope Diagram")
    
    plt.tight_layout()
    plt.suptitle("Comprehensive Beam Analysis", y=1.02)
    plt.show()
    
    # Print analysis results
    print("=== Analysis Results ===")
    print(f"Beam length: {plotter.support_positions[-1] - plotter.support_positions[0]} mm")
    print(f"Number of supports: {len(plotter.support_positions)}")
    print(f"Number of loads: {len(loads)}")
    print(f"E modulus: {deflection_calc.e_modulus} N/mm²")
    print(f"Moment of inertia: {deflection_calc.inertia_cm4} cm⁴")
    
    max_deflection, max_pos = deflection_calc.get_max_deflection()
    print(f"Maximum deflection: {max_deflection:.6f} mm at position {max_pos:.1f} mm")
    
    # Check support reactions
    reactions = plotter.reactions
    print("\nSupport reactions:")
    for pos, reaction in reactions.items():
        print(f"  Support at {pos} mm: {reaction:.2f} N")
    
    return deflection_calc


if __name__ == "__main__":
    # Run all tests
    test_simple_beam_deflection()
    test_continuous_beam_deflection()
    test_comprehensive_analysis()
    
    print("\n=== All tests completed ===") 