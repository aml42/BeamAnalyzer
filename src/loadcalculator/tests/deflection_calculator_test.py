import pytest

from loadcalculator.loads import UniformLoad
from loadcalculator.supports import Support
from loadcalculator.systembuilder import SystemBuilder
from loadcalculator.systemsolver import SystemSolver
from loadcalculator.reactionsolver import ReactionSolver
from loadcalculator.plotter import BeamPlotter
from loadcalculator.deflection_calculator import DeflectionCalculator


def _make_deflection_calc(loads, support_positions, e_modulus=2.1e11, inertia=3265e-8, num_points=2000):
    """Helper to build a DeflectionCalculator from loads and support positions (SI units)."""
    supports = [Support(pos) for pos in support_positions]
    builder = SystemBuilder(loads, supports)
    solver = SystemSolver(builder)
    reaction_solver = ReactionSolver(builder, solver)
    plotter = BeamPlotter(builder, solver, reaction_solver, num_points)
    return DeflectionCalculator(plotter, e_modulus, inertia, num_points)


def test_deflection_calculator():
    loads = [UniformLoad(19575, 0, 12)]
    support_positions = [0, 3, 6, 9, 12]
    dc = _make_deflection_calc(loads, support_positions)
    max_deflection, max_pos = dc.get_max_deflection()
    assert max_deflection == pytest.approx(-1.4e-3, abs=0.1e-3)
    assert max_pos == pytest.approx(1.3147, abs=0.05)


def test_deflection_calculator_2():
    loads = [UniformLoad(19575, 0, 13)]
    support_positions = [0, 3, 6, 9, 13]
    dc = _make_deflection_calc(loads, support_positions)
    max_deflection, max_pos = dc.get_max_deflection()
    assert max_deflection == pytest.approx(-5.12e-3, abs=0.15e-3)
