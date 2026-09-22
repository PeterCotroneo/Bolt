"""Live lightning layer: buffer incoming strikes and flush to a memory layer.

Strikes are one-off events, not tracked objects. The store adds each new strike
(deduped by id), recolours it by age every tick — a bright flash that fades
yellow -> orange -> dim — and expires it after a short window. Markers are
lightning bolts.
"""

import os
import time
from datetime import datetime, timezone

from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.QtGui import QColor
from qgis.core import (
    QgsVectorLayer,
    QgsFeature,
    QgsField,
    QgsFields,
    QgsGeometry,
    QgsPointXY,
    QgsProject,
    QgsMarkerSymbol,
    QgsSvgMarkerSymbolLayer,
    QgsSymbolLayer,
    QgsProperty,
    QgsCategorizedSymbolRenderer,
    QgsRendererCategory,
    QgsPointClusterRenderer,
    QgsMessageLog,
    Qgis,
)

LAYER_NAME = "Bolt — Live Lightning"
_BOLT_SVG = os.path.join(os.path.dirname(__file__), "bolt.svg")

_FIELDS = [
    ("age", QVariant.String),
    ("struck", QVariant.String),
    ("stations", QVariant.Int),
]
_FIELD_INDEX = {name: i for i, (name, _t) in enumerate(_FIELDS)}
_ALIASES = {"age": "Age", "struck": "Struck (UTC)", "stations": "Detectors"}

_MAP_TIP = (
    "<b>⚡ Lightning</b> · [% \"age\" %]<br/>"
    "Struck [% \"struck\" %]<br/>"
    "[% \"stations\" %] detectors reported it"
)

# Age scheme (single source of truth): (upper-bound seconds since the strike was
# received, legend label, colour). A strike flashes white, warms to yellow/orange,
# dims to red, then expires. Labels carry the range so the legend is self-explaining.
_AGE_SCHEME = [
    (8,  "Just struck (0–8s)", "#ffffff"),
    (25, "Recent (8–25s)",     "#ffd400"),
    (45, "Fading (25–45s)",    "#ff8c00"),
    (60, "Old (45–60s)",       "#c62828"),
]
MAX_AGE = float(_AGE_SCHEME[-1][0])   # strikes fade out after this many seconds
_FIRST_BUCKET = _AGE_SCHEME[0][1]
CATEGORY_COLORS = [(label, color) for _lim, label, color in _AGE_SCHEME]


def _bucket(elapsed):
    for limit, label, _color in _AGE_SCHEME:
        if elapsed < limit:
            return label
    return _AGE_SCHEME[-1][1]


class StrikeStore:
    def __init__(self):
        self._layer = None
        self._records = {}   # id -> {lat, lon, struck, stations, _t, _bucket}
        self._fid = {}       # id -> feature id
        self._pending_new = set()
        self._pending_upd = set()

    # --- layer lifecycle -------------------------------------------------
    def ensure_layer(self):
        if self._layer is not None and self._layer_valid():
            return self._layer
        fields = QgsFields()
        for name, qtype in _FIELDS:
            fields.append(QgsField(name, qtype))
        layer = QgsVectorLayer("Point?crs=EPSG:4326", LAYER_NAME, "memory")
        layer.dataProvider().addAttributes(fields.toList())
        layer.updateFields()
        for name, alias in _ALIASES.items():
            idx = layer.fields().indexOf(name)
            if idx >= 0:
                layer.setFieldAlias(idx, alias)
        layer.setMapTipTemplate(_MAP_TIP)
        self._layer = layer
        self._records.clear()
        self._fid.clear()
        self._pending_new.clear()
        self._pending_upd.clear()
        self._style(layer)
        QgsProject.instance().addMapLayer(layer)

    def _style(self, layer):
        try:
            categories = []
            for group, color in CATEGORY_COLORS:
                svg = QgsSvgMarkerSymbolLayer(_BOLT_SVG)
                svg.setSize(6)
                svg.setFillColor(QColor(color))
                svg.setStrokeColor(QColor("#333333"))
                svg.setStrokeWidth(0.2)
                sym = QgsMarkerSymbol()
                sym.changeSymbolLayer(0, svg)
                categories.append(QgsRendererCategory(group, sym, group))
            by_age = QgsCategorizedSymbolRenderer("age", categories)
            cluster = QgsPointClusterRenderer()
            cluster.setEmbeddedRenderer(by_age)
            cluster.setTolerance(3.5)
            try:
                cluster.setToleranceUnit(Qgis.RenderUnit.Millimeters)
            except (AttributeError, TypeError):
                pass
            # Colour the cluster badge by the strikes it holds (@cluster_color)
            # instead of a fixed red, so a cluster reads as recent/fading/old too.
            # Dark outline + dark count keep it legible on the light badges.
            csym = cluster.clusterSymbol()
            if csym is not None and csym.symbolLayerCount() >= 1:
                circle = csym.symbolLayer(0)
                circle.setDataDefinedProperty(
                    QgsSymbolLayer.Property.FillColor,
                    QgsProperty.fromExpression("@cluster_color"))
                if hasattr(circle, "setStrokeColor"):
                    circle.setStrokeColor(QColor("#333333"))
                if csym.symbolLayerCount() >= 2:
                    csym.symbolLayer(1).setColor(QColor("#111111"))
            layer.setRenderer(cluster)
        except Exception as exc:  # noqa: BLE001 - styling must never block data
            QgsMessageLog.logMessage(f"styling skipped: {exc}", "Bolt",
                                     Qgis.MessageLevel.Warning)

    def layer(self):
        return self._layer if self._layer_valid() else None

    def _layer_valid(self):
        try:
            return self._layer is not None and self._layer.isValid()
        except RuntimeError:
            return False

    def remove_layer(self):
        if self._layer_valid():
            QgsProject.instance().removeMapLayer(self._layer.id())
        self._layer = None
        self._records.clear()
        self._fid.clear()

    # --- ingest / flush --------------------------------------------------
    def ingest_many(self, strikes):
        now = time.time()
        for s in strikes:
            self._ingest(s, now)

    def _ingest(self, s, now):
        sid = s.get("id")
        if not sid or sid in self._records:
            return  # dedupe repeated strikes
        lat, lon = s.get("lat"), s.get("lon")
        if lat is None or lon is None:
            return
        struck = ""
        t = s.get("time")
        if t:
            try:
                struck = datetime.fromtimestamp(t / 1e9, timezone.utc).strftime(
                    "%H:%M:%S UTC")
            except (TypeError, ValueError, OSError):
                struck = ""
        self._records[sid] = {
            "lat": lat, "lon": lon, "struck": struck,
            "stations": s.get("stations", 0), "_t": now, "_bucket": _FIRST_BUCKET,
        }
        self._pending_new.add(sid)

    def _attrs(self, rec):
        return {
            _FIELD_INDEX["age"]: rec.get("_bucket", "Just struck"),
            _FIELD_INDEX["struck"]: rec.get("struck", ""),
            _FIELD_INDEX["stations"]: rec.get("stations"),
        }

    def flush(self):
        if not self._layer_valid() or (not self._pending_new and not self._pending_upd):
            return
        dp = self._layer.dataProvider()
        if self._pending_new:
            feats = []
            for sid in self._pending_new:
                rec = self._records.get(sid)
                if not rec:
                    continue
                feat = QgsFeature(self._layer.fields())
                feat.setGeometry(QgsGeometry.fromPointXY(
                    QgsPointXY(float(rec["lon"]), float(rec["lat"]))))
                attrs = [None] * len(_FIELDS)
                for idx, val in self._attrs(rec).items():
                    attrs[idx] = val
                feat.setAttributes(attrs)
                feats.append((sid, feat))
            if feats:
                ok, added = dp.addFeatures([f for _s, f in feats])
                # addFeatures preserves order; map ids back positionally
                for (sid, _f), out in zip(feats, added or []):
                    self._fid[sid] = out.id()
            self._pending_new.clear()
        if self._pending_upd:
            attr_changes = {}
            for sid in self._pending_upd:
                fid = self._fid.get(sid)
                rec = self._records.get(sid)
                if fid is not None and rec:
                    attr_changes[fid] = self._attrs(rec)
            if attr_changes:
                dp.changeAttributeValues(attr_changes)
            self._pending_upd.clear()
        self._layer.updateExtents()
        self._layer.triggerRepaint()

    def age_and_expire(self):
        """Recolour strikes by age and drop those past MAX_AGE. Call each tick."""
        if not self._layer_valid():
            return
        now = time.time()
        stale = []
        for sid, rec in self._records.items():
            elapsed = now - rec["_t"]
            if elapsed > MAX_AGE:
                stale.append(sid)
                continue
            b = _bucket(elapsed)
            if b != rec.get("_bucket"):
                rec["_bucket"] = b
                if sid in self._fid:
                    self._pending_upd.add(sid)
        fids = [self._fid[s] for s in stale if s in self._fid]
        if fids:
            self._layer.dataProvider().deleteFeatures(fids)
            self._layer.triggerRepaint()
        for s in stale:
            self._records.pop(s, None)
            self._fid.pop(s, None)

    def count(self):
        return len(self._fid)

    def retain_within(self, bbox):
        if not self._layer_valid():
            return
        lat_min, lon_min, lat_max, lon_max = bbox
        outside = []
        for sid, rec in self._records.items():
            lat, lon = rec.get("lat"), rec.get("lon")
            if not (lat_min <= lat <= lat_max and lon_min <= lon <= lon_max):
                outside.append(sid)
        fids = [self._fid[s] for s in outside if s in self._fid]
        if fids:
            self._layer.dataProvider().deleteFeatures(fids)
            self._layer.triggerRepaint()
        for s in outside:
            self._records.pop(s, None)
            self._fid.pop(s, None)
