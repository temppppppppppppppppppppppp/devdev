from .blockguide import PLUGIN as BLOCKGUIDE_PLUGIN
from .wuxguide import PLUGIN as WUXGUIDE_PLUGIN


def get_builtin_families():
    return [BLOCKGUIDE_PLUGIN, WUXGUIDE_PLUGIN]


__all__ = [
    "BLOCKGUIDE_PLUGIN",
    "WUXGUIDE_PLUGIN",
    "get_builtin_families",
]
