from collections.abc import Iterator

from shotforge.i18n import get_translator


def flatten_keys(data: dict, prefix: str = "") -> Iterator[str]:
    for key, value in data.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            yield from flatten_keys(value, path)
        else:
            yield path


def test_locale_keys_are_aligned():
    translator = get_translator()
    zh_keys = set(flatten_keys(translator.locales["zh"]))
    en_keys = set(flatten_keys(translator.locales["en"]))

    assert zh_keys == en_keys


def test_translator_formats_and_falls_back():
    translator = get_translator()

    assert translator.t("zh", "web.correction_plans.title") == "修正计划"
    assert translator.t("en", "web.correction_plans.title") == "Correction Plans"
    assert translator.t("fr", "web.correction_plans.title") == "Correction Plans"
    assert (
        translator.t("en", "agents.suggestion.strategy", dimensions="Action", correction_type="action")
        == "Apply targeted action correction for: Action."
    )
