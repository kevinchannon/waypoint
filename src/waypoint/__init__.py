try:
    from importlib.metadata import version

    __version__ = version("waypoint")
except Exception:
    __version__ = "0.0.0.dev0+local"  # Fallback for development