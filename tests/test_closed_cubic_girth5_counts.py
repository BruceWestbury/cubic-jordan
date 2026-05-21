def test_closed_cubic_girth5_counts():
    expected = {
        4: 0,
        6: 0,
        8: 0,
        10: 1,
        12: 2,
        14: 9,
        16: 49,
        18: 455,
    }

    for t, exp in expected.items():
        assert count_closed_graphs(t) == exp