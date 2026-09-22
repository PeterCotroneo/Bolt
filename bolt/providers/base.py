"""Provider abstraction for Bolt.

A provider delivers live lightning strikes. Strikes are one-off events, not
tracked objects, so a provider just emits each detected strike (in small batches)
and the store adds them and lets them fade.

Normalised strike dict (keys a provider emits; all required except stations):
    id (str)         - unique key for the strike (dedupes repeats)
    lat, lon (float) - strike location (WGS84)
    time (int)       - strike time, nanoseconds since the Unix epoch
    stations (int)   - how many detectors reported it (a rough strength proxy)
"""

from qgis.PyQt.QtCore import QObject, pyqtSignal


class StrikeProvider(QObject):
    """Abstract live-lightning source. Subclasses implement start()/stop()."""

    strikes_update = pyqtSignal(list)  # a batch of normalised strike dicts
    status_changed = pyqtSignal(str)
    error = pyqtSignal(str)

    id = "base"
    label = "Abstract provider"
    help_text = ""
    config_fields = []

    def __init__(self, settings=None, parent=None):
        super().__init__(parent)
        self.settings = settings or {}

    @classmethod
    def needs_config(cls):
        return bool(cls.config_fields)

    def start(self, bboxes):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def update_area(self, bboxes):
        # strikes arrive globally; the store clips to the view
        pass
