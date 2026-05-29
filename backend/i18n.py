"""Locale-aware string lookup with ContextVar-scoped per-session override.

기본 로케일은 DEMO_LOCALE 환경변수(기본 'ko'). 키별 누락 시 한국어로 fallback.
WebSocket 세션에서 set_locale() 로 해당 비동기 컨텍스트에 한정해 로케일을 바꿀 수 있다.
"""
from __future__ import annotations

import os
from contextvars import ContextVar
from typing import Any

from locales import en as _en
from locales import ko as _ko

_LOCALES: dict[str, dict] = {"ko": _ko.STRINGS, "en": _en.STRINGS}
_FALLBACK = "ko"


def _normalize(locale: str | None) -> str:
    if not locale:
        return _FALLBACK
    key = locale.strip().lower()
    return key if key in _LOCALES else _FALLBACK


_DEFAULT_LOCALE: str = _normalize(os.environ.get("DEMO_LOCALE"))
_current_locale: ContextVar[str] = ContextVar("demo_locale", default=_DEFAULT_LOCALE)


def get_default_locale() -> str:
    return _DEFAULT_LOCALE


def get_locale() -> str:
    return _current_locale.get()


def set_locale(locale: str | None) -> str:
    """현재 비동기 컨텍스트에 한정해 로케일을 설정한다. 정규화된 값을 반환한다."""
    resolved = _normalize(locale)
    _current_locale.set(resolved)
    return resolved


def available_locales() -> list[str]:
    return list(_LOCALES.keys())


def t(key: str, /, **kwargs: Any) -> Any:
    """키에 해당하는 문자열(또는 리스트) 반환. str 일 때만 kwargs로 .format() 적용."""
    locale = get_locale()
    table = _LOCALES.get(locale, _LOCALES[_FALLBACK])
    value = table.get(key)
    if value is None and locale != _FALLBACK:
        value = _LOCALES[_FALLBACK].get(key)
    if value is None:
        return key  # 디버깅 용이성: 누락된 키는 그대로 노출
    if kwargs and isinstance(value, str):
        try:
            return value.format(**kwargs)
        except Exception:
            return value
    return value
