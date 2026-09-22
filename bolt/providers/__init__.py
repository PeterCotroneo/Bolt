"""Provider registry.

Adding a lightning source: implement StrikeProvider in a new module, declare its
``config_fields`` if it needs any, and register it below. The plugin builds its
provider dropdown and settings dialog from PROVIDERS + each provider's
config_fields — nothing else needs to change.
"""

from .base import StrikeProvider
from .blitzortung import BlitzortungProvider

# id -> provider class (order shown in the dropdown; the first is the default)
PROVIDERS = {
    BlitzortungProvider.id: BlitzortungProvider,
}

__all__ = ["StrikeProvider", "BlitzortungProvider", "PROVIDERS"]
