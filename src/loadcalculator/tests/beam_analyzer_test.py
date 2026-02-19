import pytest

from loadcalculator.beam_analyzer import BeamAnalyzer
from loadcalculator.loads import UniformLoad

def test_beam_analyzer():
    support_positions = [0.0, 5.0]
    loads = [UniformLoad(magnitude=1, start=0, end=5)]
    inertia = 138
    analyzer = BeamAnalyzer(support_positions, loads, inertia)
    results = analyzer.analyze()
    assert results['reactions'] is not None
    assert results['moments_at_supports'] is not None
    assert results['max_moments_per_span'] is not None
    assert results['max_shear_per_span'] is not None
    assert results['max_deflection_per_span'] is not None

def test_beam_analyzer_12m():
    support_positions = [0.0, 3.0, 6.0, 9.0, 12.0]
    loads = [UniformLoad(magnitude=19575, start=0, end=12)]
    inertia = 3265
    analyzer = BeamAnalyzer(support_positions, loads, inertia)
    results = analyzer.analyze()
    assert results['max_deflection_per_span'][0]['max_deflection'] == pytest.approx(-1.4, abs=0.15)
    assert results['max_deflection_per_span'][1]['max_deflection'] == pytest.approx(-0.42, abs=0.05)
    assert results['max_deflection_per_span'][2]['max_deflection'] == pytest.approx(-0.42, abs=0.05)
    assert results['max_deflection_per_span'][3]['max_deflection'] == pytest.approx(-1.4, abs=0.15)

    assert results['max_deflection_per_span'][0]['max_deflection_position'] == pytest.approx(1.31, abs=0.01)
    assert results['max_deflection_per_span'][1]['max_deflection_position'] == pytest.approx(4.62, abs=0.01)
    assert results['max_deflection_per_span'][2]['max_deflection_position'] == pytest.approx(7.38, abs=0.01)
    assert results['max_deflection_per_span'][3]['max_deflection_position'] == pytest.approx(10.69, abs=0.01)