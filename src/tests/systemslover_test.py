import pytest
import numpy as np
from mechanics.basic_mechanics.systemsolver import SystemSolver
from mechanics.basic_mechanics.systembuilder import SystemBuilder
from mechanics.basic_mechanics.loads import UniformLoad, TriangularLoad
from mechanics.basic_mechanics.supports import Support

# Test group 1: Basic system solver https://mathalino.com/reviewer/strength-materials/problem-813-continuous-beam-three-moment-equation

# Test case 1: Basic system solver
def test_basic_system_solver():
    builder = SystemBuilder([TriangularLoad(0, 1400, 0, 4)], [Support(0), Support(4), Support(8)])
    solver = SystemSolver(builder)
    moments = solver.solve_moments()
    moment_at_4 = float(moments[4])
    assert moment_at_4 == pytest.approx(-746.666, abs=0.1)

# Test case 2: System solver with triangular load
def test_basic_system_solver_triangular_and_punctual():
    builder = SystemBuilder([TriangularLoad(0, 1400, 0, 4), UniformLoad(90000, 4.99,5), UniformLoad(800, 6,8)], [Support(0), Support(4), Support(8)])
    solver = SystemSolver(builder)
    moments = solver.solve_moments()
    moment_at_4 = float(moments[4])
    assert moment_at_4 == pytest.approx(-1391.98, abs=1)

# Test case 3: Continuous decreasing trinangular load
def test_basic_system_solver_continuous_decreasing_triangular_load():
    builder = SystemBuilder([TriangularLoad(0, 200, 0, 20)], [Support(0), Support(10), Support(20)])
    solver = SystemSolver(builder)
    moments = solver.solve_moments()
    moment_at_10 = float(moments[10])
    assert moment_at_10 == pytest.approx(-1250, abs=1)

# Test case 4: 4 Support system with uniform load on middle span
def test_basic_system_solver_4_support_system_with_uniform_load_on_middle_span():
    builder = SystemBuilder([UniformLoad(1000, 4,8)], [Support(0), Support(4), Support(8), Support(12)])
    solver = SystemSolver(builder)
    moments = solver.solve_moments()
    moment_at_4 = float(moments[4])
    moment_at_8 = float(moments[8])
    assert moment_at_4 == pytest.approx(-800, abs=1)
    assert moment_at_8 == pytest.approx(-800, abs=1)

# Test case 5: 4 Support system with uniform load on middle span, unequal spans
def test_basic_system_solver_4_support_system_with_uniform_load_on_middle_span_unequal_spans():
    builder = SystemBuilder([UniformLoad(1000, 3,10)], [Support(0), Support(3), Support(10), Support(12)])
    solver = SystemSolver(builder)
    moments = solver.solve_moments()
    moment_at_3 = float(moments[3])
    moment_at_10 = float(moments[10])
    assert moment_at_3 == pytest.approx(-3032.9, abs=1)
    assert moment_at_10 == pytest.approx(-3584, abs=1)

# Test case 6: 4 Support system with uniform load on middle span, unequal spans
def test_basic_system_solver_4_support_system_with_triangular_increasing_load():
    builder = SystemBuilder([TriangularLoad(0, 1000, 1,11)], [Support(0), Support(3), Support(10), Support(12)])
    solver = SystemSolver(builder)
    moments = solver.solve_moments()
    moment_at_3 = float(moments[3])
    moment_at_10 = float(moments[10])
    assert moment_at_3 == pytest.approx(-1509.19, abs=1)
    assert moment_at_10 == pytest.approx(-2204, abs=1)
