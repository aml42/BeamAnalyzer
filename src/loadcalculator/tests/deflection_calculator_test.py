import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loadcalculator.loads import UniformLoad, TriangularLoad
from loadcalculator.supports import Support
from loadcalculator.systembuilder import SystemBuilder
from loadcalculator.systemsolver import SystemSolver
from loadcalculator.reactionsolver import ReactionSolver
from loadcalculator.plotter import BeamPlotter
from loadcalculator.deflection_calculator import DeflectionCalculatorSI
import matplotlib.pyplot as plt
import pytest

def test_deflection_calculator():
    """Test deflection calculation for a simple supported beam with uniform load.

    Uses a 4 m span (4000 mm) so deflection is measurable. With L=4 mm, deflection
    would be ~1.6e-8 mm (L^4 scaling). For w=10 N/mm, E=210000, I=16000 cm^4:
    delta_max = 5*w*L^4/(384*E*I) ≈ 1.0 mm at mid-span.
    """
    loads = [UniformLoad(19575, 0, 12)]  # 10 N/m over 4 m span
    support_positions = [0, 3, 6, 9, 12]
    deflection_calc = DeflectionCalculatorSI(loads, support_positions, e_modulus=210000, inertia=3265)
    max_deflection, max_pos = deflection_calc.get_max_deflection()
    assert max_deflection == pytest.approx(-1.4, abs=0.1)  # downward = negative
    assert max_pos == pytest.approx(1314.7, abs=50.0)  # mid-span at 2000 mm


