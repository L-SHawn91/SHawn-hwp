from shawn_hwp.converters.strategy_router import choose_route


def test_choose_route():
    assert choose_route("HWPX", "DOCX") == "hwpx-to-docx"
