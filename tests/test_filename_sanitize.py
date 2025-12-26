from bot.domain.normalize import deduplicate_preserve_order, sanitize_filename


def test_sanitize_filename_removes_invalid_symbols():
    assert sanitize_filename('сыр 9% (моцарелла):*?"<>|') == "сыр 9% (моцарелла)"


def test_sanitize_filename_limits_length():
    long_name = "a" * 200
    assert len(sanitize_filename(long_name, max_length=80)) == 80


def test_sanitize_filename_falls_back_to_food_for_invalid_only():
    assert sanitize_filename(':*?"<>|') == "food"


def test_sanitize_filename_strips_trailing_dots():
    assert sanitize_filename("сыр...") == "сыр"


def test_sanitize_filename_handles_unicode_and_spaces():
    assert sanitize_filename("  Сыр 🧀  deluxe  ") == "Сыр deluxe"


def test_sanitize_filename_truncates_without_empty_result():
    value = "яблоки " * 20
    result = sanitize_filename(value, max_length=30)
    assert result
    assert len(result) == 30
    assert not result.endswith(" ")


def test_deduplicate_preserve_order_keeps_first_occurrence():
    items = ["молоко", "сыр", "молоко", "хлеб"]
    assert deduplicate_preserve_order(items) == ["молоко", "сыр", "хлеб"]
