from app.models import MatchMode, normalize_text, text_matches


def test_normalize_text():
    assert normalize_text("  Я \n  тут  ") == "Я тут"


def test_exact_matching():
    assert text_matches(" Я   тут ", "Я тут", MatchMode.EXACT)
    assert not text_matches('Нажми "Я тут"', "Я тут", MatchMode.EXACT)


def test_contains_matching():
    assert text_matches("Кнопка: Я тут", "Я тут", MatchMode.CONTAINS)


def test_case_insensitive_modes():
    assert text_matches("CONFIRM", "confirm", MatchMode.CASE_INSENSITIVE_EXACT)
    assert text_matches(
        "Please Confirm now",
        "confirm",
        MatchMode.CASE_INSENSITIVE_CONTAINS,
    )
