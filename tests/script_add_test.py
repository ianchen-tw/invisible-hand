from hand.scripts.add import unique


def test_unique():
    assert unique([1, 1, 2, 2, 2, 3]) == [1, 2, 3]
