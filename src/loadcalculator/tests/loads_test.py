from mechanics.basic_mechanics.loads import TriangularLoad, UniformLoad
import pytest

# Test group 1: Uniform load------------------------------                               

# Test case 1: Uniform load on the whole left span
def test_uniform_load_on_whole_span():
   uniform_load = UniformLoad(10, 0, 4)
   left_component = uniform_load.load_components_left_span(4, 0, 4)
   right_component = uniform_load.load_components_right_span(4, 0, 4)

   assert left_component == 160
   assert right_component == 160

# Test case 2: partial uniform load on the left span
def test_partial_uniform_load():
    uniform_load = UniformLoad(10, 1, 3)
    left_component = uniform_load.load_components_left_span(4, 1, 3)
    right_component = uniform_load.load_components_right_span(4, 1, 3)
    assert left_component == 110
    assert right_component == 110

# Test group 2: Triangular increasing load------------------------------

# Test case 1: Triangular increasing load on the whole left span
def test_triangular_increasing_load_on_whole_span():
    triangular_increasing_load = TriangularLoad(0,10,0,4)
    left_component = triangular_increasing_load.load_components_left_span(4, 0, 4)
    right_component = triangular_increasing_load.load_components_right_span(4, 0, 4)

    assert left_component == pytest.approx(85.33, abs=0.01)
    assert right_component == pytest.approx(74.67, abs=0.01)

# Test case 2: partial triangular increasing load on the left span
def test_partial_triangular_increasing_load():
    triangular_increasing_load = TriangularLoad(0,100,3,9)
    left_component = triangular_increasing_load.load_components_left_span(9, 3, 9)
    right_component = triangular_increasing_load.load_components_right_span(9, 3, 9)

    assert left_component == pytest.approx(6120, abs=0.01)
    assert right_component == pytest.approx(4680, abs=0.01)

# Test case 3: Triangular decreasing load on the whole left span
def test_triangular_decreasing_load_on_whole_span():
    triangular_decreasing_load = TriangularLoad(10,0,0,4)
    left_component = triangular_decreasing_load.load_components_left_span(4, 0, 4)
    right_component = triangular_decreasing_load.load_components_right_span(4, 0, 4)

    assert left_component == pytest.approx(74.67, abs=0.01)
    assert right_component == pytest.approx(85.33, abs=0.01)

# Test case 4: partial triangular decreasing load on the left span
def test_partial_triangular_decreasing_load():
    triangular_decreasing_load = TriangularLoad(100,0,3,9)
    left_component = triangular_decreasing_load.load_components_left_span(9, 3, 9)
    right_component = triangular_decreasing_load.load_components_right_span(9, 3, 9)

    assert left_component == pytest.approx(8280, abs=0.01)
    assert right_component == pytest.approx(7920, abs=0.01)

# # Test group 3: Punctual load------------------------------

# # Test case 1: Punctual load on the whole left span
# def test_centred_punctual_loads():
#     punctual_load = PunctualLoad(10, 2)
#     left_component = punctual_load.load_components_left_span(4)
#     right_component = punctual_load.load_components_right_span(4)

#     assert left_component == 60
#     assert right_component == 60

# # Test case 2: Off centred punctual loads
# def test_off_centred_punctual_loads():
#     punctual_load = PunctualLoad(10, 1)
#     left_component = punctual_load.load_components_left_span(4)
#     right_component = punctual_load.load_components_right_span(4)

#     assert left_component == 37.5
#     assert right_component == 52.5