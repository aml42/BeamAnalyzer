"""Hand-verified textbook cases for cantilever (overhang) support.

Each case has a closed-form solution from elementary statics; results are
asserted against those values. Sign convention: sagging positive, upward
reactions positive, downward loads positive.
"""
import numpy as np
import pytest

from loadcalculator import (
    BeamAnalyzer,
    UniformLoad,
    TriangularLoad,
)


# ---------------------------------------------------------------------------
# Case 1: Single inner span + right overhang, uniform load on overhang only.
# Supports at 0 and L=10, overhang to L+c=12, w=10 on overhang only.
# Hand calc:
#   M_right = -w·c²/2 = -20
#   R_left  = -w·c²/(2L) = -2  (downward — beam tries to lift)
#   R_right =  w·c·(2L+c)/(2L) = 22
# ---------------------------------------------------------------------------

def test_right_overhang_load_only():
    L, c, w = 10.0, 2.0, 10.0
    analyzer = BeamAnalyzer(
        support_positions=[0.0, L],
        loads=[UniformLoad(magnitude=w, start=L, end=L + c)],
    )
    res = analyzer.analyze()

    assert res['reactions'][0.0] == pytest.approx(-w * c**2 / (2 * L), rel=1e-6)
    assert res['reactions'][L] == pytest.approx(w * c * (2 * L + c) / (2 * L), rel=1e-6)
    assert res['moments_at_supports'][0.0] == pytest.approx(0.0, abs=1e-9)
    assert res['moments_at_supports'][L] == pytest.approx(-w * c**2 / 2, rel=1e-6)
    # Sum of reactions equals total applied load.
    assert sum(res['reactions'].values()) == pytest.approx(w * c, rel=1e-6)


# ---------------------------------------------------------------------------
# Case 2: Single inner span + right overhang, uniform load over the entire beam.
# Supports at 0 and L=10, beam extends to L+c=12. Uniform w over [0, L+c].
# Hand calc:
#   M_right = -w·c²/2
#   R_left  =  w·(L-c)·(L+c)/(2L) = 48
#   R_right =  w·(L+c)²/(2L)      = 72
# ---------------------------------------------------------------------------

def test_right_overhang_full_uniform_load():
    L, c, w = 10.0, 2.0, 10.0
    analyzer = BeamAnalyzer(
        support_positions=[0.0, L],
        loads=[UniformLoad(magnitude=w, start=0.0, end=L + c)],
    )
    res = analyzer.analyze()

    assert res['reactions'][0.0] == pytest.approx(w * (L - c) * (L + c) / (2 * L), rel=1e-6)
    assert res['reactions'][L] == pytest.approx(w * (L + c) ** 2 / (2 * L), rel=1e-6)
    assert res['moments_at_supports'][L] == pytest.approx(-w * c**2 / 2, rel=1e-6)
    assert sum(res['reactions'].values()) == pytest.approx(w * (L + c), rel=1e-6)


# ---------------------------------------------------------------------------
# Case 3: Two-span continuous beam + right overhang, load on overhang only.
# Supports at 0, 10, 20; overhang to 22; w=10 on [20, 22].
# Three-moment for internal support 10:
#   2·M_2·(10+10) + M_3·10 = 0  (no inner-span loads, M_1 = 0)
#   M_3 = -w·c²/2 = -20
#   40·M_2 - 200 = 0  →  M_2 = 5
# Reactions:
#   span [0,10]: R_0 = (M_2 - M_1)/L = 0.5; R_10_partial = -0.5
#   span [10,20]: R_10_partial = (M_3 - M_2)/L = -2.5; R_20_inner = +2.5
#   plus overhang weight wc=20 added to R_20: R_20 = 22.5
# ---------------------------------------------------------------------------

def test_two_span_with_right_overhang():
    analyzer = BeamAnalyzer(
        support_positions=[0.0, 10.0, 20.0],
        loads=[UniformLoad(magnitude=10.0, start=20.0, end=22.0)],
    )
    res = analyzer.analyze()

    assert res['moments_at_supports'][0.0] == pytest.approx(0.0, abs=1e-9)
    assert res['moments_at_supports'][10.0] == pytest.approx(5.0, rel=1e-6)
    assert res['moments_at_supports'][20.0] == pytest.approx(-20.0, rel=1e-6)

    assert res['reactions'][0.0] == pytest.approx(0.5, rel=1e-6)
    assert res['reactions'][10.0] == pytest.approx(-3.0, rel=1e-6)
    assert res['reactions'][20.0] == pytest.approx(22.5, rel=1e-6)
    assert sum(res['reactions'].values()) == pytest.approx(20.0, rel=1e-6)


# ---------------------------------------------------------------------------
# Case 4: Symmetric beam, two supports + overhang each side, uniform load full length.
# Supports at 0 and L=10; overhangs of length c=2 each side; w=10 over [-2, 12].
# By symmetry: R_left = R_right = w(L+2c)/2 = 70.
# End moments: -w·c²/2 = -20 (each).
# ---------------------------------------------------------------------------

def test_symmetric_double_overhang():
    L, c, w = 10.0, 2.0, 10.0
    analyzer = BeamAnalyzer(
        support_positions=[0.0, L],
        loads=[UniformLoad(magnitude=w, start=-c, end=L + c)],
    )
    res = analyzer.analyze()

    expected_R = w * (L + 2 * c) / 2
    assert res['reactions'][0.0] == pytest.approx(expected_R, rel=1e-6)
    assert res['reactions'][L] == pytest.approx(expected_R, rel=1e-6)
    assert res['moments_at_supports'][0.0] == pytest.approx(-w * c**2 / 2, rel=1e-6)
    assert res['moments_at_supports'][L] == pytest.approx(-w * c**2 / 2, rel=1e-6)
    assert sum(res['reactions'].values()) == pytest.approx(w * (L + 2 * c), rel=1e-6)


# ---------------------------------------------------------------------------
# Case 5: Straddling-load split equivalence.
# A single load that spans both overhangs and the main beam must produce the
# same physical results as passing three pre-split loads explicitly.
# ---------------------------------------------------------------------------

def test_straddling_uniform_split_equivalence():
    supports = [0.0, 10.0]
    a = BeamAnalyzer(
        support_positions=supports,
        loads=[UniformLoad(magnitude=10.0, start=-2.0, end=12.0)],
    )
    b = BeamAnalyzer(
        support_positions=supports,
        loads=[
            UniformLoad(magnitude=10.0, start=-2.0, end=0.0),
            UniformLoad(magnitude=10.0, start=0.0, end=10.0),
            UniformLoad(magnitude=10.0, start=10.0, end=12.0),
        ],
    )
    res_a = a.analyze()
    res_b = b.analyze()
    for pos in supports:
        assert res_a['reactions'][pos] == pytest.approx(res_b['reactions'][pos], rel=1e-6)
        assert res_a['moments_at_supports'][pos] == pytest.approx(
            res_b['moments_at_supports'][pos], rel=1e-6, abs=1e-9
        )


# ---------------------------------------------------------------------------
# Case 6: Triangular load straddling end supports.
# TriangularLoad(0, 30, 0, 10) — linear from 0 at x=0 to 30 at x=10.
# Supports at [3, 7]; left overhang [0, 3], right overhang [7, 10].
# load_function(x) = 3x.
# Hand-computed end moments (sagging-positive convention):
#   M_left  = -∫_0^3 3x·(3 - x) dx = -[9x²/2 - x³]_0^3 = -13.5
#   M_right = -∫_7^{10} 3x·(x - 7) dx = -[x³ - 21x²/2]_7^{10} = -121.5
# Total downward load on overhangs:
#   W_left  = ∫_0^3 3x dx = 13.5  → adds to R_3
#   W_right = ∫_7^{10} 3x dx = 76.5 → adds to R_7
# Sum of all reactions equals total load 150 (= ∫_0^{10} 3x dx).
# ---------------------------------------------------------------------------

def test_triangular_straddling_endpoints():
    analyzer = BeamAnalyzer(
        support_positions=[3.0, 7.0],
        loads=[TriangularLoad(magnitude_start=0, magnitude_end=30, start=0.0, end=10.0)],
    )
    res = analyzer.analyze()

    assert res['moments_at_supports'][3.0] == pytest.approx(-13.5, rel=1e-6)
    assert res['moments_at_supports'][7.0] == pytest.approx(-121.5, rel=1e-6)
    # Conservation of vertical force.
    assert sum(res['reactions'].values()) == pytest.approx(150.0, rel=1e-6)


# ---------------------------------------------------------------------------
# Sanity: deflection at the free end of a cantilever beam matches textbook.
# For a simply-supported span with a right overhang of length c carrying a
# uniform load only on the overhang, the tip deflection is approximately
# δ_tip = -w·c³·(c + L) / (24·E·I)  (Roark, downward).
# We use a coarse tolerance because the integration is numerical.
# ---------------------------------------------------------------------------

def test_overhang_slope_continuity():
    """The deflection curve must have no kinks at cantilever-adjacent supports.

    Verified by computing the central-difference numerical slope on the
    grid points immediately flanking each end support and asserting they
    agree to tight tolerance.
    """
    L, c, w = 10.0, 2.0, 10.0
    analyzer = BeamAnalyzer(
        support_positions=[0.0, L],
        loads=[UniformLoad(magnitude=w, start=-c, end=L + c)],  # both overhangs loaded
        e_modulus=2.1e11,
        inertia=138e-8,
        num_points=4000,
    )
    analyzer.analyze()
    x_arr, defl = analyzer.get_deflection_values()

    def _slope_around(x_target):
        idx = int(np.argmin(np.abs(x_arr - x_target)))
        # central differences just left and just right of the support
        slope_left = (defl[idx] - defl[idx - 2]) / (x_arr[idx] - x_arr[idx - 2])
        slope_right = (defl[idx + 2] - defl[idx]) / (x_arr[idx + 2] - x_arr[idx])
        return slope_left, slope_right

    for support in (0.0, L):
        sl, sr = _slope_around(support)
        # Slopes are O(1e-4) rad in magnitude for this beam; assert mismatch is
        # an order of magnitude tighter than that.
        assert abs(sl - sr) < 1e-6, (
            f"Slope discontinuity at support x={support}: left={sl}, right={sr}"
        )


def test_overhang_tip_deflection_textbook():
    L, c, w = 10.0, 2.0, 10.0
    E, I = 2.1e11, 138e-8
    analyzer = BeamAnalyzer(
        support_positions=[0.0, L],
        loads=[UniformLoad(magnitude=w, start=L, end=L + c)],
        e_modulus=E,
        inertia=I,
        num_points=4000,
    )
    analyzer.analyze()
    _, defl_arr = analyzer.get_deflection_values()
    # tip deflection = value at the free end (last grid index)
    tip = float(defl_arr[-1])
    # Closed-form tip deflection:
    #   inner-span rotation at right support due to M_R = -wc²/2:
    #     θ_R = M_R · L / (3 E I) = -w·c²·L / (6 E I)
    #   cantilever own bending: δ_cant = -w·c⁴/(8 E I)
    #   carrying-over rotation contribution: θ_R · c
    expected_tip = (-w * c**4 / (8 * E * I)) + (-w * c**2 * L / (6 * E * I)) * c
    assert tip == pytest.approx(expected_tip, rel=0.01)
