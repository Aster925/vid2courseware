from core.analyze import estimate_tokens, jaccard, ngrams


def test_estimate_tokens_uses_word_count_heuristic():
    assert estimate_tokens("one two three four") == 5


def test_four_gram_jaccard_detects_overlap():
    left = "alpha beta gamma delta epsilon"
    right = "alpha beta gamma delta zeta"

    assert ngrams(left) == {
        ("alpha", "beta", "gamma", "delta"),
        ("beta", "gamma", "delta", "epsilon"),
    }
    assert jaccard(left, right) == 1 / 3
