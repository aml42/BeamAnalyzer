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
    loads = [UniformLoad(19575, 0, 12)]  #  N/m over m span
    support_positions = [0, 3, 6, 9, 12]
    deflection_calc = DeflectionCalculatorSI(loads, support_positions, e_modulus=210000, inertia=3265)
    max_deflection, max_pos = deflection_calc.get_max_deflection()
    assert max_deflection == pytest.approx(-1.4, abs=0.1)  # downward = negative
    assert max_pos == pytest.approx(1314.7, abs=50.0)  # mid-span at 2000 mm


def test_deflection_calculator_2():
    loads = [UniformLoad(19575, 0, 13)]  #  N/m over m span
    support_positions = [0, 3, 6, 9, 13]
    deflection_calc = DeflectionCalculatorSI(loads, support_positions, e_modulus=210000, inertia=3265)
    max_deflection, max_pos = deflection_calc.get_max_deflection()
    # deflection_calc.plot_deflection()
    # plt.show()
    assert max_deflection == pytest.approx(-5.12, abs=0.15)  