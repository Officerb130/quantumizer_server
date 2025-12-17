"""Central place to setup needed config

All config via environment variables for now
"""
import os

_config_cache = None

from pydantic import BaseSettings

class ThemeConfig(BaseSettings):

    BOOTSWATCH: str ="cyborg"
    CARD_CLASS: str ="bg-light"
    CHART_TOOLTIP_BG: str = "#000000"

    CHART_COLOR_R1_START: str = "#faf20a"
    CHART_COLOR_R1_END: str = "#b30000"

    CHART_COLOR_R2_START: str = "#9eed95"
    CHART_COLOR_R2_END: str = "#196619"

    NAVBAR_TEXT_CLASS: str = "bg-dark"
    NAVBAR_CLASS: str = "navbar-dark"

    TABLE_CLASS: str = "table-light"
    TABLE_SECONDARY_CLASS: str = "table-secondary"
    TABLE_FONT_SIZE: str = "14px"
    TABLE_FONT_SIZE_SMALL: str = "12px"

    BADGE_PRIMARY: str = "bg-secondary"

    BUTTON_CLASS: str = "btn-outline-primary"

    COLOR_GREEN: str = "#54C756"
    COLOR_RED: str = "#DD4659"

    class Config:
        extra = 'allow'
        env_file = '.theme'
        env_file_encoding = 'utf-8'

def get() -> ThemeConfig:
    global _config_cache
    if not _config_cache:
        _config_cache = ThemeConfig()
    return _config_cache