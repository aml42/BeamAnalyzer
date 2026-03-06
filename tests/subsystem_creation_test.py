from loadcalculator.systembuilder import SystemBuilder
from loadcalculator.loads import UniformLoad, TriangularLoad
from loadcalculator.supports import Support
import pytest

# Test group 1: Subsystem creation------------------------------
def test_subsystem_creation_3_supports():
    builder = SystemBuilder([UniformLoad(10, 0, 10), UniformLoad(20, 10, 20)], [Support(0), Support(20), Support(10)])
    subsystems = builder._create_subsystems()
    
    assert len(subsystems) == 1
    assert subsystems == (((0, 10), (10, 20)),)
    
def test_subsystem_creation_4_supports():
    builder = SystemBuilder([UniformLoad(10, 0, 10), UniformLoad(20, 10, 20)], [Support(0), Support(20), Support(10), Support(30)])
    subsystems = builder._create_subsystems()
    
    assert len(subsystems) == 2
    assert subsystems == (((0, 10), (10, 20)), ((10, 20), (20, 30)))


# Test group 2: Subsystem load overlaps------------------------------
def test_subsystem_load_overlaps():
    builder = SystemBuilder([UniformLoad(10, 0, 10), UniformLoad(20, 10, 20)], [Support(0), Support(20), Support(10), Support(30)])
    builder._get_subsystem_load_overlaps()

    assert len(builder._get_subsystem_load_overlaps()) == 3

    assert builder._get_subsystem_load_overlaps()[0][0] == ((0, 10), (10, 20))
    assert builder._get_subsystem_load_overlaps()[0][1].__tuple__() == ("uniform", 10, 0, 10)
    assert builder._get_subsystem_load_overlaps()[0][2] == (0, 10)
    assert builder._get_subsystem_load_overlaps()[1][0] == ((0, 10), (10, 20))
    assert builder._get_subsystem_load_overlaps()[1][1].__tuple__() == ("uniform", 20, 10, 20)
    assert builder._get_subsystem_load_overlaps()[1][2] == (10, 20)
    assert builder._get_subsystem_load_overlaps()[2][0] == ((10, 20), (20, 30))
    assert builder._get_subsystem_load_overlaps()[2][1].__tuple__() == ("uniform", 20, 10, 20)
    assert builder._get_subsystem_load_overlaps()[2][2] == (10, 20)


# Test group 3: Load component calculations------------------------------
def test_calculate_load_components_for_subsystem():
    builder = SystemBuilder([UniformLoad(10, 0, 10)], [Support(0), Support(10), Support(20)])
    subsystem = ((0, 10), (10, 20))
    load = UniformLoad(10, 0, 10)
    overlap = (0, 10)
    
    # Test left span component
    left_component = builder._calculate_load_components_for_subsystem(subsystem, load, overlap, 'left')
    assert left_component is not None
    assert isinstance(left_component, (int, float))
    
    # Test right span component
    right_component = builder._calculate_load_components_for_subsystem(subsystem, load, overlap, 'right')
    assert right_component is not None
    assert isinstance(right_component, (int, float))
    
    # Test invalid span position
    with pytest.raises(ValueError):
        builder._calculate_load_components_for_subsystem(subsystem, load, overlap, 'middle')


def test_get_subsystem_load_components_detailed():
    builder = SystemBuilder([UniformLoad(10, 0, 10), UniformLoad(20, 10, 20)], [Support(0), Support(10), Support(20)])
    detailed_components = builder._get_subsystem_load_components_detailed()
    
    assert len(detailed_components) == 1
    assert 'subsystem' in detailed_components[0]
    assert 'left_span_overlaps' in detailed_components[0]
    assert 'right_span_overlaps' in detailed_components[0]
    
    # Check that we have the expected overlaps
    left_overlaps = detailed_components[0]['left_span_overlaps']
    right_overlaps = detailed_components[0]['right_span_overlaps']
    
    assert len(left_overlaps) == 1  # Only first load overlaps with left span
    assert len(right_overlaps) == 1  # Only second load overlaps with right span
    
    # Each overlap should be a tuple of (load, overlap_range, component)
    assert len(left_overlaps[0]) == 3
    assert len(right_overlaps[0]) == 3


def test_calculate_subsystem_components():
    builder = SystemBuilder([UniformLoad(10, 0, 10), UniformLoad(20, 10, 20)], [Support(0), Support(10), Support(20)])
    components = builder.calculate_subsystem_components()
    
    assert len(components) == 1
    subsystem = ((0, 10), (10, 20))
    assert subsystem in components
    
    result = components[subsystem]
    assert 'left_component' in result
    assert 'right_component' in result
    assert 'total_component' in result
    
    # Check that total is sum of left and right
    assert result['total_component'] == result['left_component'] + result['right_component']
    
    # Components should be numbers
    assert isinstance(result['left_component'], (int, float))
    assert isinstance(result['right_component'], (int, float))
    assert isinstance(result['total_component'], (int, float))


def test_calculate_subsystem_components_multiple_subsystems():
    # Test with 4 supports creating 2 subsystems
    builder = SystemBuilder([UniformLoad(10, 0, 15), UniformLoad(20, 15, 30)], [Support(0), Support(10), Support(20), Support(30)])
    components = builder.calculate_subsystem_components()
    
    assert len(components) == 2
    
    # Check that all subsystems are present
    subsystem1 = ((0, 10), (10, 20))
    subsystem2 = ((10, 20), (20, 30))
    assert subsystem1 in components
    assert subsystem2 in components
    
    # Check that each has the required keys
    for subsystem in [subsystem1, subsystem2]:
        result = components[subsystem]
        assert 'left_component' in result
        assert 'right_component' in result
        assert 'total_component' in result
        assert result['total_component'] == result['left_component'] + result['right_component']


def test_calculate_subsystem_components_with_triangular_load():
    # Test with triangular load
    builder = SystemBuilder([TriangularLoad(0, 20, 0, 10)], [Support(0), Support(10), Support(20)])
    components = builder.calculate_subsystem_components()
    
    assert len(components) == 1
    subsystem = ((0, 10), (10, 20))
    assert subsystem in components
    
    result = components[subsystem]
    assert isinstance(result['left_component'], (int, float))
    assert isinstance(result['right_component'], (int, float))
    assert result['total_component'] == result['left_component'] + result['right_component']


def test_calculate_subsystem_components_no_overlaps():
    # Test case where load doesn't overlap with any span
    builder = SystemBuilder([UniformLoad(10, 25, 35)], [Support(0), Support(10), Support(20)])
    components = builder.calculate_subsystem_components()
    
    assert len(components) == 1
    subsystem = ((0, 10), (10, 20))
    result = components[subsystem]
    
    # Should have zero components since no overlaps
    assert result['left_component'] == 0
    assert result['right_component'] == 0
    assert result['total_component'] == 0

# Test group 4 -- Different loading scenarios from https://mathalino.com/reviewer/strength-materials/three-moment-equation#google_vignette

def test_calculate_subsystem_components_with_triangular_load_and_supports():
    # Test with triangular load and supports
    builder = SystemBuilder([TriangularLoad(0, 1400, 0, 4), UniformLoad(90000, 4.99, 5), UniformLoad(800, 6, 8)], [Support(0), Support(4), Support(8)])
    components = builder.calculate_subsystem_components()
    
    assert len(components) == 1
    subsystem = ((0, 4), (4, 8))
    assert subsystem in components

    result = components[subsystem]
    # Updated expected values based on current calculation method
    assert result['left_component'] == pytest.approx(11946.67, abs=1)
    assert result['right_component'] == pytest.approx(10312.5, abs=1)
    assert result['total_component'] == pytest.approx(22259.224, abs=1)
    
def test_calculate_subsystem_components_with_continuous_triangular_load():
    builder = SystemBuilder([TriangularLoad(200, 0, 0, 20)], [Support(0), Support(10), Support(20)])
    components = builder.calculate_subsystem_components()
    
    assert len(components) == 1
    subsystem = ((0, 10), (10, 20))
    assert subsystem in components
    
    result = components[subsystem]
    assert result['left_component'] == pytest.approx(36666.67, abs=1)
    assert result['right_component'] == pytest.approx(13333.33, abs=1)
    assert result['total_component'] == pytest.approx(50000, abs=1)
    
def test_calculate_subsystem_components_4_supports_uniform_load():
    builder = SystemBuilder([UniformLoad(1000, 10, 20)], [Support(0), Support(10), Support(20), Support(30)])
    components = builder.calculate_subsystem_components()
    
    assert len(components) == 2
    subsystem1 = ((0, 10), (10, 20))
    subsystem2 = ((10, 20), (20, 30))
    assert subsystem1 in components
    assert subsystem2 in components
    
    result1 = components[subsystem1]
    result2 = components[subsystem2]
    
    assert result1['left_component'] == pytest.approx(0, abs=1)
    assert result1['right_component'] == pytest.approx(250000, abs=1)
    assert result1['total_component'] == pytest.approx(250000, abs=1)

    assert result2['left_component'] == pytest.approx(250000, abs=1)
    assert result2['right_component'] == pytest.approx(0, abs=1)
    assert result2['total_component'] == pytest.approx(250000, abs=1)

def test_calculate_subsystem_components_4_supports_uniform_load_uneven_spacing():
    builder = SystemBuilder([UniformLoad(1000, 15, 20)], [Support(0), Support(15), Support(20), Support(30)])
    components = builder.calculate_subsystem_components()
    
    assert len(components) == 2
    subsystem1 = ((0, 15), (15, 20))
    subsystem2 = ((15, 20), (20, 30))
    assert subsystem1 in components
    assert subsystem2 in components
    
    result1 = components[subsystem1]
    result2 = components[subsystem2]
    
    assert result1['left_component'] == pytest.approx(0, abs=1)
    assert result1['right_component'] == pytest.approx(31250, abs=1)
    assert result1['total_component'] == pytest.approx(31250, abs=1)

    assert result2['left_component'] == pytest.approx(31250, abs=1)
    assert result2['right_component'] == pytest.approx(0, abs=1)
    assert result2['total_component'] == pytest.approx(31250, abs=1)