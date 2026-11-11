"""Independent integration checks for the distribution drawn in chapter 14."""
import pytest
from visuals.scenes.ch14_reference_figures import BUDGET, rss, uniform_three_pdf


def test_uniform_sum_normalization_variance_and_coverage():
    # Midpoint integration verifies the piecewise density without Monte Carlo noise.
    step = .001
    points = [-3 + (i+.5)*step for i in range(6000)]
    mass = sum(uniform_three_pdf(x)*step for x in points)
    variance = sum(x*x*uniform_three_pdf(x)*step for x in points)
    covered = sum(uniform_three_pdf(x)*step for x in points if abs(x) <= 2)
    assert mass == pytest.approx(1, abs=1e-6)
    # Three independent U[-1,1] variables each have variance 1/3.
    assert variance == pytest.approx(1, abs=1e-6)
    assert covered == pytest.approx(23/24, abs=1e-6)
    assert uniform_three_pdf(-3.1) == uniform_three_pdf(3.1) == 0


def test_budget_preserves_units_and_separates_sum_from_sigma():
    assert rss(BUDGET)**2 == pytest.approx(.006725)
    assert sum(BUDGET) == pytest.approx(.175)
    assert rss(BUDGET) < .1 < 3*rss(BUDGET)
    assert rss([v*1000 for v in BUDGET]) == pytest.approx(1000*rss(BUDGET))
