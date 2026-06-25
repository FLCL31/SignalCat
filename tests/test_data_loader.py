from utils.data_loader import load_universe, select_representative_universe


def test_load_universe_counts():
    universe = load_universe("LIST.md")
    assert len(universe) == 211
    assert universe["ticker"].nunique() == 211
    assert universe["category"].nunique() == 24


def test_select_representative_universe_limit():
    universe = load_universe("LIST.md")
    selected = select_representative_universe(universe, 12)
    assert len(selected) == 12
    assert selected["ticker"].nunique() == 12
