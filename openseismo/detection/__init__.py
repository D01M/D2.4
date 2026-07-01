"""Automatic detection package for OpenSeismo."""

from .auto_detector import AutoEarthquakeDetector, DetectionEvent, StationTrigger

__all__ = ["AutoEarthquakeDetector", "DetectionEvent", "StationTrigger"]