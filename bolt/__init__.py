def classFactory(iface):
    """Entry point required by QGIS to load the plugin."""
    from .bolt_plugin import BoltPlugin
    return BoltPlugin(iface)
