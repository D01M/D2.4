"""Station metadata manager for OpenSeismo Desktop.

This module loads station metadata from JSON, validates entries, keeps fast
lookup caches, and exposes safe live-status update helpers.
It does not contain any rendering or detection logic.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


LOGGER = logging.getLogger(__name__)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_station_file() -> Path:
    return _repo_root() / "data" / "stations" / "stations.json"


def _normalize_list(value) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        parts = [item.strip() for item in value.replace(";", ",").split(",")]
        return [item for item in parts if item]
    if isinstance(value, Sequence):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()]


def _parse_timestamp(value) -> Optional[datetime]:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


def _status_normalize(value: Optional[str]) -> str:
    status = str(value or "unknown").strip().lower()
    aliases = {
        "operational": "online",
        "active": "online",
        "up": "online",
        "ok": "online",
        "warn": "delayed",
        "warning": "delayed",
    }
    return aliases.get(status, status or "unknown")


def _signal_quality_from_noise(noise_level: Optional[float]) -> str:
    if noise_level is None:
        return "unknown"
    if noise_level < 20:
        return "excellent"
    if noise_level < 40:
        return "good"
    if noise_level < 65:
        return "fair"
    return "poor"


@dataclass
class StationRecord:
    id: str
    network: str
    code: str
    name: str
    latitude: float
    longitude: float
    elevation_m: Optional[float] = None
    country: Optional[str] = None
    region: Optional[str] = None
    channels: List[str] = field(default_factory=list)
    provider: Optional[str] = None
    source: Optional[str] = None
    status: str = "unknown"
    priority: int = 0
    tags: List[str] = field(default_factory=list)
    last_seen: Optional[datetime] = None
    noise_level: Optional[float] = None
    coverage_radius_km: Optional[float] = None
    latency_seconds: Optional[float] = None
    signal_quality: Optional[str] = None

    def to_dict(self) -> Dict[str, object]:
        last_seen_iso = self.last_seen.isoformat().replace("+00:00", "Z") if self.last_seen else None
        normalized_status = _status_normalize(self.status)
        noise_level = self.noise_level
        latency_seconds = self.latency_seconds
        if latency_seconds is None and self.last_seen is not None:
            latency_seconds = max(0.0, (datetime.now(timezone.utc) - self.last_seen).total_seconds())

        return {
            "id": self.id,
            "network": self.network,
            "code": self.code,
            "name": self.name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "lat": self.latitude,
            "lon": self.longitude,
            "elevation_m": self.elevation_m,
            "country": self.country,
            "region": self.region,
            "channels": list(self.channels),
            "provider": self.provider,
            "source": self.source,
            "status": normalized_status,
            "health": normalized_status,
            "priority": self.priority,
            "tags": list(self.tags),
            "last_seen": last_seen_iso,
            "noise_level": noise_level,
            "coverage_radius_km": self.coverage_radius_km,
            "latency_seconds": latency_seconds,
            "signal_quality": self.signal_quality or _signal_quality_from_noise(noise_level),
        }


class StationManager:
    """Load, validate, cache, and update station metadata."""

    def __init__(self, station_file: Optional[Path | str] = None):
        self.station_file = Path(station_file) if station_file else _default_station_file()
        self._stations_by_id: Dict[str, StationRecord] = {}
        self._station_keys: Dict[Tuple[str, str], str] = {}
        self._load_error: Optional[str] = None
        self.load_station_metadata()

    @property
    def load_error(self) -> Optional[str]:
        return self._load_error

    def load_station_metadata(self, station_file: Optional[Path | str] = None) -> List[Dict[str, object]]:
        if station_file is not None:
            self.station_file = Path(station_file)

        self._stations_by_id.clear()
        self._station_keys.clear()
        self._load_error = None

        path = self.station_file
        if not path.exists():
            self._load_error = f"Station metadata file not found: {path}"
            LOGGER.warning(self._load_error)
            return []

        try:
            with path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except Exception as exc:
            self._load_error = f"Failed to read station metadata: {exc}"
            LOGGER.warning(self._load_error)
            return []

        stations = payload.get("stations", payload) if isinstance(payload, dict) else payload
        if not isinstance(stations, list):
            self._load_error = "Station metadata must be a list or a dictionary with a 'stations' key"
            LOGGER.warning(self._load_error)
            return []

        normalized: List[Dict[str, object]] = []
        for entry in stations:
            record = self._normalize_station_entry(entry)
            if record is None:
                continue
            dedupe_key = (record.network.lower(), record.code.lower())
            if dedupe_key in self._station_keys:
                LOGGER.warning("Skipping duplicate station entry for %s/%s", record.network, record.code)
                continue
            self._station_keys[dedupe_key] = record.id
            self._stations_by_id[record.id] = record
            normalized.append(record.to_dict())

        return normalized

    def _normalize_station_entry(self, entry) -> Optional[StationRecord]:
        if not isinstance(entry, dict):
            LOGGER.warning("Skipping invalid station entry (not a dict): %r", entry)
            return None

        code = str(entry.get("code", "")).strip()
        network = str(entry.get("network", "")).strip()
        name = str(entry.get("name", "")).strip()
        station_id = str(entry.get("id") or f"{network}:{code}").strip()
        latitude = entry.get("latitude", entry.get("lat"))
        longitude = entry.get("longitude", entry.get("lon"))
        channels = _normalize_list(entry.get("channels"))

        if not code or not network:
            LOGGER.warning("Skipping station with missing code/network: %r", entry)
            return None
        if latitude is None or longitude is None:
            LOGGER.warning("Skipping station with missing coordinates: %s/%s", network, code)
            return None
        if not self._valid_latlon(latitude, longitude):
            LOGGER.warning("Skipping station with invalid coordinates: %s/%s", network, code)
            return None
        if not channels:
            LOGGER.warning("Skipping station with no channels: %s/%s", network, code)
            return None

        last_seen = _parse_timestamp(entry.get("last_seen"))
        noise_level = entry.get("noise_level")
        priority = entry.get("priority", 0)
        coverage_radius_km = entry.get("coverage_radius_km")
        latency_seconds = entry.get("latency_seconds")
        provider = entry.get("provider") or entry.get("source")
        source = entry.get("source") or entry.get("provider")
        status = _status_normalize(entry.get("status") or entry.get("health"))
        signal_quality = entry.get("signal_quality")

        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except (TypeError, ValueError):
            LOGGER.warning("Skipping station with non-numeric coordinates: %s/%s", network, code)
            return None

        try:
            priority = int(priority)
        except (TypeError, ValueError):
            priority = 0

        try:
            if noise_level is not None:
                noise_level = float(noise_level)
        except (TypeError, ValueError):
            noise_level = None

        try:
            if coverage_radius_km is not None:
                coverage_radius_km = float(coverage_radius_km)
        except (TypeError, ValueError):
            coverage_radius_km = None

        try:
            if latency_seconds is not None:
                latency_seconds = float(latency_seconds)
        except (TypeError, ValueError):
            latency_seconds = None

        tags = _normalize_list(entry.get("tags"))

        return StationRecord(
            id=station_id,
            network=network,
            code=code,
            name=name or code,
            latitude=latitude,
            longitude=longitude,
            elevation_m=entry.get("elevation_m"),
            country=entry.get("country"),
            region=entry.get("region"),
            channels=channels,
            provider=provider,
            source=source,
            status=status,
            priority=priority,
            tags=tags,
            last_seen=last_seen,
            noise_level=noise_level,
            coverage_radius_km=coverage_radius_km,
            latency_seconds=latency_seconds,
            signal_quality=signal_quality,
        )

    @staticmethod
    def _valid_latlon(latitude, longitude) -> bool:
        try:
            lat = float(latitude)
            lon = float(longitude)
        except (TypeError, ValueError):
            return False
        return -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0

    def list_stations(self) -> List[Dict[str, object]]:
        return [record.to_dict() for record in self._stations_by_id.values()]

    def get_station_by_id(self, station_id: str) -> Optional[Dict[str, object]]:
        record = self._stations_by_id.get(str(station_id))
        return record.to_dict() if record else None

    def get_station_record(self, station_id: str) -> Optional[StationRecord]:
        return self._stations_by_id.get(str(station_id))

    def get_station_by_network_code(self, network: str, code: str) -> Optional[Dict[str, object]]:
        key = (str(network).lower(), str(code).lower())
        station_id = self._station_keys.get(key)
        return self.get_station_by_id(station_id) if station_id else None

    def filter_stations(
        self,
        network: Optional[Iterable[str] | str] = None,
        country: Optional[Iterable[str] | str] = None,
        region: Optional[Iterable[str] | str] = None,
        status: Optional[Iterable[str] | str] = None,
        channel: Optional[Iterable[str] | str] = None,
        tag: Optional[Iterable[str] | str] = None,
        recent_minutes: Optional[int] = None,
        active_only: bool = False,
    ) -> List[Dict[str, object]]:
        network_values = {item.lower() for item in _normalize_list(network)} if network else None
        country_values = {item.lower() for item in _normalize_list(country)} if country else None
        region_values = {item.lower() for item in _normalize_list(region)} if region else None
        status_values = {item.lower() for item in _normalize_list(status)} if status else None
        channel_values = {item.lower() for item in _normalize_list(channel)} if channel else None
        tag_values = {item.lower() for item in _normalize_list(tag)} if tag else None

        cutoff = None
        if recent_minutes and recent_minutes > 0:
            cutoff = datetime.now(timezone.utc).timestamp() - (recent_minutes * 60)

        active_statuses = {"online", "triggering", "delayed"}

        filtered: List[Dict[str, object]] = []
        for record in self._stations_by_id.values():
            station = record.to_dict()
            station_status = str(station.get("status") or "unknown").lower()

            if network_values and str(station.get("network", "")).lower() not in network_values:
                continue
            if country_values and str(station.get("country", "")).lower() not in country_values:
                continue
            if region_values and str(station.get("region", "")).lower() not in region_values:
                continue
            if status_values and station_status not in status_values:
                continue
            if channel_values and not any(str(item).lower() in channel_values for item in station.get("channels", [])):
                continue
            if tag_values and not any(str(item).lower() in tag_values for item in station.get("tags", [])):
                continue
            if active_only and station_status not in active_statuses:
                continue
            if cutoff is not None:
                last_seen = _parse_timestamp(station.get("last_seen"))
                if last_seen is None or last_seen.timestamp() < cutoff:
                    continue

            filtered.append(station)

        return sorted(filtered, key=lambda item: (int(item.get("priority", 0)) * -1, str(item.get("name", ""))))

    def get_active_stations(self, recent_minutes: Optional[int] = None) -> List[Dict[str, object]]:
        return self.filter_stations(active_only=True, recent_minutes=recent_minutes)

    def _update_station(self, station_id: str, **changes) -> Optional[Dict[str, object]]:
        record = self._stations_by_id.get(str(station_id))
        if record is None:
            LOGGER.warning("Station update ignored for unknown station: %s", station_id)
            return None

        for key, value in changes.items():
            if hasattr(record, key) and value is not None:
                setattr(record, key, value)

        return record.to_dict()

    def mark_online(self, station_id: str) -> Optional[Dict[str, object]]:
        return self._update_station(station_id, status="online")

    def mark_offline(self, station_id: str) -> Optional[Dict[str, object]]:
        return self._update_station(station_id, status="offline")

    def mark_delayed(self, station_id: str) -> Optional[Dict[str, object]]:
        return self._update_station(station_id, status="delayed")

    def mark_triggering(self, station_id: str) -> Optional[Dict[str, object]]:
        return self._update_station(station_id, status="triggering", last_seen=datetime.now(timezone.utc))

    def update_noise_level(self, station_id: str, value) -> Optional[Dict[str, object]]:
        try:
            noise_level = float(value)
        except (TypeError, ValueError):
            LOGGER.warning("Ignoring invalid noise update for %s: %r", station_id, value)
            return None
        return self._update_station(station_id, noise_level=noise_level)

    def update_last_seen(self, station_id: str, timestamp) -> Optional[Dict[str, object]]:
        parsed = _parse_timestamp(timestamp)
        if parsed is None:
            LOGGER.warning("Ignoring invalid last_seen update for %s: %r", station_id, timestamp)
            return None
        return self._update_station(station_id, last_seen=parsed)
