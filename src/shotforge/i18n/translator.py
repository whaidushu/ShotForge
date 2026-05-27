from __future__ import annotations

import json
from functools import lru_cache
from importlib.resources import files
from typing import Any


class Translator:
    def __init__(self, locales: dict[str, dict[str, Any]], fallback_language: str = "en"):
        self.locales = locales
        self.fallback_language = fallback_language

    def t(self, language: str, key: str, **kwargs: Any) -> Any:
        value = self._lookup(language, key)
        if value is None:
            value = self._lookup(self.fallback_language, key)
        if value is None:
            return key
        if isinstance(value, str) and kwargs:
            return value.format(**kwargs)
        return value

    def namespace(self, language: str, prefix: str) -> dict[str, Any]:
        value = self.t(language, prefix)
        return value if isinstance(value, dict) else {}

    def _lookup(self, language: str, key: str) -> Any:
        current: Any = self.locales.get(language)
        if current is None:
            return None
        for part in key.split("."):
            if not isinstance(current, dict) or part not in current:
                return None
            current = current[part]
        return current


@lru_cache
def get_translator() -> Translator:
    locale_root = files("shotforge.i18n.locales")
    locales = {}
    for language in ("zh", "en"):
        locales[language] = json.loads(
            locale_root.joinpath(f"{language}.json").read_text(encoding="utf-8")
        )
    return Translator(locales=locales)
