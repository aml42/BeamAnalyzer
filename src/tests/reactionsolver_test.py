import pytest
import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reactionsolver import ReactionSolver
from systemsolver import SystemSolver
from systembuilder import SystemBuilder
from loads import UniformLoad, TriangularLoad
from supports import Support

def test_basic_reaction_solver_triangular_load_3_support():
    """Test ReactionSolver with a simple triangular load case"""
    builder = SystemBuilder([TriangularLoad(0, 1400, 0, 4)], [Support(0), Support(4), Support(8)])
    solver = SystemSolver(builder)
    reaction_solver = ReactionSolver(builder, solver)
    
    reactions = reaction_solver.calculate_support_reactions()
    moments = solver.solve_moments()
    reactions = reaction_solver.calculate_support_reactions()
    
    assert reactions[0] == pytest.approx(746.667, abs=0.1)
    assert reactions[4] == pytest.approx(2240, abs=0.1)
    assert reactions[8] == pytest.approx(-186.667, abs=0.1)

def test_basic_reaction_solver_triangular_load_3_support_triangular_load():
    """Test ReactionSolver with a simple triangular load case"""
    builder = SystemBuilder([TriangularLoad(0, 1400, 0, 8)], [Support(0), Support(4), Support(8)])
    solver = SystemSolver(builder)
    reaction_solver = ReactionSolver(builder, solver)
    
    reactions = reaction_solver.calculate_support_reactions()
    moments = solver.solve_moments()
    reactions = reaction_solver.calculate_support_reactions()
    
    assert reactions[0] == pytest.approx(116.67, abs=0.1)
    assert reactions[4] == pytest.approx(3500, abs=0.1)
    assert reactions[8] == pytest.approx(1983.333, abs=0.1)

def test_basic_reaction_solver_triangular_load_4_support_triangular_load():
    """Test ReactionSolver with a simple triangular load case"""
    builder = SystemBuilder([TriangularLoad(0, 1400, 0, 8)], [Support(0), Support(4), Support(8), Support(12)])
    solver = SystemSolver(builder)
    reaction_solver = ReactionSolver(builder, solver)
    
    reactions = reaction_solver.calculate_support_reactions()
    moments = solver.solve_moments()
    reactions = reaction_solver.calculate_support_reactions()
    
    assert reactions[0] == pytest.approx(164.888, abs=1)
    assert reactions[4] == pytest.approx(3210.651, abs=1)
    assert reactions[8] == pytest.approx(2417.321, abs=1)
    assert reactions[12] == pytest.approx(-192.888, abs=1)

def test_basic_reaction_solver_triangular_load_4_support_triangular_load_2():
        """Test ReactionSolver with a simple triangular load case"""
        builder = SystemBuilder([TriangularLoad(0, 1400, 1, 10)], [Support(0), Support(3), Support(4), Support(12)])
        solver = SystemSolver(builder)
        reaction_solver = ReactionSolver(builder, solver)
        
        reactions = reaction_solver.calculate_support_reactions()
        moments = solver.solve_moments()
        reactions = reaction_solver.calculate_support_reactions()
        
        assert reactions[0] == pytest.approx(293.889, abs=1)
        assert reactions[3] == pytest.approx(-6670.648, abs=1)
        assert reactions[4] == pytest.approx(11001.173, abs=1)
        assert reactions[12] == pytest.approx(1675.549, abs=1)


def test_single_span_reaction_solver():
    builder = SystemBuilder([TriangularLoad(0, 1400, 0, 4)], [Support(0), Support(4)])
    solver = SystemSolver(builder)
    reaction_solver = ReactionSolver(builder, solver)
    
    reactions = reaction_solver.calculate_support_reactions()
    moments = solver.solve_moments()
    reactions = reaction_solver.calculate_support_reactions()
    
    assert reactions[0] == pytest.approx(933, abs=1)
    assert reactions[4] == pytest.approx(1866.667, abs=1)

def test_single_span_reaction_solver_2():
    builder = SystemBuilder([UniformLoad(1000, 1, 2)], [Support(0), Support(4)])
    solver = SystemSolver(builder)
    reaction_solver = ReactionSolver(builder, solver)
    
    reactions = reaction_solver.calculate_support_reactions()
    moments = solver.solve_moments()
    reactions = reaction_solver.calculate_support_reactions()
    
    assert reactions[0] == pytest.approx(625, abs=1)
    assert reactions[4] == pytest.approx(375, abs=1)