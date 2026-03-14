from shawn_hwp.qa.scoring import total_weight


def test_total_weight():
    assert total_weight() == 100
