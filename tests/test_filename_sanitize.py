from bot.domain.normalize import deduplicate_preserve_order, sanitize_filename


def test_sanitize_filename_removes_invalid_symbols():
    assert sanitize_filename('сыр 9% (моцарелла):*?"<>|') == "сыр 9% (моцарелла)"


def test_sanitize_filename_limits_length():
    long_name = "a" * 200
    assert len(sanitize_filename(long_name, max_length=80)) == 80


def test_deduplicate_preserve_order_keeps_first_occurrence():
    items = ["молоко", "сыр", "молоко", "хлеб"]
    assert deduplicate_preserve_order(items) == ["молоко", "сыр", "хлеб"]
