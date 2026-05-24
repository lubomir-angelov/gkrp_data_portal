"""Language/locale management for the NiceGUI application.

Provides a global language state (EN / BG) persisted in general storage,
and a helper to look up translated strings from the LOCALE dict.
"""

from __future__ import annotations

from nicegui import app, ui

LANG_KEY = "gkrp_lang"
LANG_OPTIONS = ["en", "bg"]


def get_lang() -> str:
    """Return the current language code (defaults to 'bg')."""
    return app.storage.general.get(LANG_KEY, "bg") or "bg"


def set_lang(lang: str) -> None:
    """Persist a language choice and emit a JS event for cross-page sync."""
    if lang not in LANG_OPTIONS:
        lang = "bg"
    app.storage.general[LANG_KEY] = lang
    # Emit a custom event so any open page can react to the change
    ui.run_javascript(
        f"""
        window.dispatchEvent(new CustomEvent('gkrp-lang-change', {{detail: '{lang}'}}));
        """
    )


def t(key: str) -> str:
    """Translate a LOCALE key for the current language.

    Looks up ``LOCALE[f"{key}_{lang}"]`` first (EN suffixed variant),
    then falls back to the base key (BG default).
    """
    lang = get_lang()
    suffixed = f"{key}_{lang}"
    if lang == "en":
        from gkrp_data_portal.ui.pages.analytics_common import LOCALE

        return LOCALE.get(suffixed, LOCALE.get(key, key))
    # bg is the default (base keys)
    from gkrp_data_portal.ui.pages.analytics_common import LOCALE

    return LOCALE.get(key, key)


def toggle_lang() -> None:
    """Switch between 'en' and 'bg'."""
    current = get_lang()
    next_lang = "bg" if current == "en" else "en"
    set_lang(next_lang)


def get_lang_button_label() -> str:
    """Return the language code to display on the toggle button.

    Shows the *target* language (what you'll switch TO).
    """
    current = get_lang()
    return "BG" if current == "en" else "EN"
