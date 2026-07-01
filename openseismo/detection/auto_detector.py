"""Automatic earthquake detection utilities.

This module is intentionally independent from Flask and the browser UI.
It performs heuristic, automatic trigger detection and produces unreviewed
events only. Official confirmation is still required.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from math import sqrt, isfinite
from statistics import mean
from typing import TYPE_CHECKING, Deque, Dict, Iterable, List, Optional, Tuple
from uuid import uuid4

if TYPE_CHECKING:
    from openseismo.stations.station_manager import StationManager


@dataclass(frozen=True)
class StationTrigger:
    """A single station trigger from an automatic detector.

    This is not reviewed agency data. It is a local trigger candidate.
    """

    station_id: str
    station_name: str
    latitude: float
    longitude: float
    trigger_time: datetime
    peak_amplitude: float
    noise_rms: float
    snr: float
    sta_lta: float


@dataclass(frozen=True)
class DetectionEvent:
    """An automatic multi-station detection event.

    Location is approximate and confidence is heuristic only.
    Official confirmation is still required.
    """

    event_id: str
    origin_time: datetime
    triggers: List[StationTrigger] = field(default_factory=list)
    confidence: float = 0.0
    estimated_latitude: float = 0.0
    estimated_longitude: float = 0.0
    status: str = "automatic"
    notes: str = (
        "AUTOMATIC DETECTION — UNREVIEWED. "
        "Not reviewed agency data. Location is approximate. "
        "Confidence is heuristic. Official confirmation is still required."
    )


@dataclass
class _StationState:
    latitude: float
    longitude: float
    name: str
    sample_rate_hz: float
    samples: Deque[Tuple[datetime, float]]
    last_trigger_time: Optional[datetime] = None
    status: str = "unknown"


class AutoEarthquakeDetector:
    """Heuristic automatic detector for station waveform samples."""

    def __init__(
        self,
        minimum_station_count: int = 4,
        coincidence_window_seconds: float = 8.0,
        cooldown_seconds: float = 120.0,
        min_snr: float = 3.0,
        min_sta_lta: float = 2.5,
        sta_window_seconds: float = 1.0,
        lta_window_seconds: float = 10.0,
    ):
        self.minimum_station_count = maximum_of_four(minimum_station_count)
        self.coincidence_window_seconds = float(coincidence_window_seconds)
        self.cooldown_seconds = float(cooldown_seconds)
        self.min_snr = float(min_snr)
        self.min_sta_lta = float(min_sta_lta)
        self.sta_window_seconds = float(sta_window_seconds)
        self.lta_window_seconds = float(lta_window_seconds)
        self._stations: Dict[str, _StationState] = {}
        self._recent_triggers: Deque[StationTrigger] = deque()
        self._last_event_time: Optional[datetime] = None

    def register_station(
        self,
        station_id: str,
        latitude: float,
        longitude: float,
        station_name: str = "Unknown station",
        sample_rate_hz: float = 20.0,
        status: str = "unknown",
    ) -> None:
        """Register a station and its approximate geographic location."""

        if not station_id:
            raise ValueError("station_id is required")
        if not self._coordinates_valid(latitude, longitude):
            raise ValueError("station coordinates must be valid latitude/longitude values")
        if sample_rate_hz <= 0:
            raise ValueError("sample_rate_hz must be positive")

        buffer_size = max(int(sample_rate_hz * self.lta_window_seconds * 2), 32)
        self._stations[station_id] = _StationState(
            latitude=float(latitude),
            longitude=float(longitude),
            name=station_name or station_id,
            sample_rate_hz=float(sample_rate_hz),
            samples=deque(maxlen=buffer_size),
            status=str(status or "unknown").lower(),
        )

    def register_station_metadata(
        self,
        stations: Iterable[dict],
        include_offline: bool = False,
        sample_rate_hz: float = 20.0,
    ) -> int:
        """Register a batch of station metadata records.

        Offline stations are skipped by default so automatic detection only uses
        live or active stations unless explicitly configured otherwise.
        """

        count = 0
        for station in stations:
            if not isinstance(station, dict):
                continue
            status = str(station.get("status") or station.get("health") or "unknown").lower()
            if not include_offline and status == "offline":
                continue

            station_id = str(station.get("id") or f"{station.get('network', '')}:{station.get('code', '')}").strip()
            latitude = station.get("latitude", station.get("lat"))
            longitude = station.get("longitude", station.get("lon"))
            try:
                latitude = float(latitude)
                longitude = float(longitude)
            except (TypeError, ValueError):
                continue

            if not station_id or not self._coordinates_valid(latitude, longitude):
                continue

            self.register_station(
                station_id=station_id,
                latitude=float(latitude),
                longitude=float(longitude),
                station_name=str(station.get("name") or station.get("code") or station_id),
                sample_rate_hz=float(station.get("sample_rate_hz") or sample_rate_hz),
                status=status,
            )
            count += 1

        return count

    def register_from_station_manager(
        self,
        station_manager: "StationManager",
        include_offline: bool = False,
        recent_minutes: Optional[int] = None,
        sample_rate_hz: float = 20.0,
    ) -> int:
        """Register stations from a StationManager snapshot.

        This keeps the detector aligned with the current station metadata while
        avoiding offline stations by default.
        """

        stations = station_manager.filter_stations(
            active_only=not include_offline,
            recent_minutes=recent_minutes,
        ) if not include_offline else station_manager.list_stations()
        return self.register_station_metadata(stations, include_offline=include_offline, sample_rate_hz=sample_rate_hz)

    def sync_from_station_manager(
        self,
        station_manager: "StationManager",
        include_offline: bool = False,
        recent_minutes: Optional[int] = None,
        sample_rate_hz: float = 20.0,
    ) -> int:
        """Replace detector station registration with the latest metadata."""

        self._stations.clear()
        return self.register_from_station_manager(
            station_manager,
            include_offline=include_offline,
            recent_minutes=recent_minutes,
            sample_rate_hz=sample_rate_hz,
        )

    def get_registered_station_ids(self) -> List[str]:
        return sorted(self._stations.keys())

    def add_sample(
        self,
        station_id: str,
        sample: float,
        timestamp: Optional[datetime] = None,
    ) -> Optional[DetectionEvent]:
        """Add one waveform sample and return a detection event if formed."""

        state = self._stations.get(station_id)
        if state is None:
            return None

        ts = timestamp or datetime.utcnow()
        state.samples.append((ts, float(sample)))

        trigger = self._evaluate_station(state, station_id)
        if trigger is not None:
            self._recent_triggers.append(trigger)
            self._prune_triggers(ts)
            return self._maybe_build_event(ts)

        self._prune_triggers(ts)
        return None

    def add_samples_batch(
        self,
        station_id: str,
        samples: Iterable[float],
        timestamps: Optional[Iterable[datetime]] = None,
    ) -> List[DetectionEvent]:
        """Add a batch of samples and return any formed events."""

        events: List[DetectionEvent] = []
        timestamp_iter = iter(timestamps) if timestamps is not None else None

        for sample in samples:
            ts = next(timestamp_iter) if timestamp_iter is not None else None
            event = self.add_sample(station_id, sample, ts)
            if event is not None:
                events.append(event)

        return events

    def _evaluate_station(
        self,
        state: _StationState,
        station_id: str,
    ) -> Optional[StationTrigger]:
        sample_count = len(state.samples)
        sta_count = max(3, int(state.sample_rate_hz * self.sta_window_seconds))
        lta_count = max(sta_count * 4, int(state.sample_rate_hz * self.lta_window_seconds))

        if sample_count < lta_count + sta_count:
            return None

        ordered_samples = list(state.samples)
        lta_window = [value for _, value in ordered_samples[-(lta_count + sta_count):-sta_count]]
        sta_window = [value for _, value in ordered_samples[-sta_count:]]

        noise_rms = rms(lta_window)
        sta_rms = rms(sta_window)
        peak_amplitude = max(abs(value) for value in sta_window)

        if noise_rms <= 1e-9:
            if sta_rms <= 1e-9:
                return None
            snr = sta_rms / 1e-9
        else:
            snr = sta_rms / noise_rms

        sta_lta = sta_rms / max(noise_rms, 1e-9)

        if sta_lta < self.min_sta_lta or snr < self.min_snr:
            return None

        trigger_time = ordered_samples[-1][0]
        if state.last_trigger_time and (trigger_time - state.last_trigger_time).total_seconds() < self.cooldown_seconds:
            return None

        state.last_trigger_time = trigger_time
        return StationTrigger(
            station_id=station_id,
            station_name=state.name,
            latitude=state.latitude,
            longitude=state.longitude,
            trigger_time=trigger_time,
            peak_amplitude=peak_amplitude,
            noise_rms=noise_rms,
            snr=snr,
            sta_lta=sta_lta,
        )

    def _maybe_build_event(self, now: datetime) -> Optional[DetectionEvent]:
        self._prune_triggers(now)

        if self._last_event_time and (now - self._last_event_time).total_seconds() < self.cooldown_seconds:
            return None

        triggers = self._coincident_triggers(now)
        if len(triggers) < self.minimum_station_count:
            return None

        if not self._geographic_sanity_check(triggers):
            return None

        confidence = self._confidence_score(triggers)
        latitude, longitude = self._weighted_centroid(triggers)

        event = DetectionEvent(
            event_id=f"auto-{uuid4().hex}",
            origin_time=min(trigger.trigger_time for trigger in triggers),
            triggers=triggers,
            confidence=confidence,
            estimated_latitude=latitude,
            estimated_longitude=longitude,
            status="automatic",
        )

        self._last_event_time = now
        self._recent_triggers.clear()
        return event

    def _coincident_triggers(self, now: datetime) -> List[StationTrigger]:
        window_start = now - timedelta(seconds=self.coincidence_window_seconds)
        latest_by_station: Dict[str, StationTrigger] = {}

        for trigger in self._recent_triggers:
            if trigger.trigger_time < window_start:
                continue
            previous = latest_by_station.get(trigger.station_id)
            if previous is None or trigger.trigger_time > previous.trigger_time:
                latest_by_station[trigger.station_id] = trigger

        return sorted(latest_by_station.values(), key=lambda item: item.trigger_time)

    def _prune_triggers(self, now: datetime) -> None:
        window_start = now - timedelta(seconds=self.coincidence_window_seconds)
        while self._recent_triggers and self._recent_triggers[0].trigger_time < window_start:
            self._recent_triggers.popleft()

    def _geographic_sanity_check(self, triggers: List[StationTrigger]) -> bool:
        coordinates = [(trigger.latitude, trigger.longitude) for trigger in triggers]
        for latitude, longitude in coordinates:
            if not self._coordinates_valid(latitude, longitude):
                return False

        if len(set(coordinates)) == 1:
            return False

        return True

    def _confidence_score(self, triggers: List[StationTrigger]) -> float:
        station_ratio = min(1.0, len(triggers) / float(self.minimum_station_count))
        avg_snr = mean(trigger.snr for trigger in triggers)
        avg_sta_lta = mean(trigger.sta_lta for trigger in triggers)
        time_spread = (max(trigger.trigger_time for trigger in triggers) - min(trigger.trigger_time for trigger in triggers)).total_seconds()

        snr_score = min(1.0, max(0.0, (avg_snr - self.min_snr) / max(self.min_snr, 1.0)))
        sta_lta_score = min(1.0, max(0.0, (avg_sta_lta - self.min_sta_lta) / max(self.min_sta_lta, 1.0)))
        coincidence_score = max(0.0, 1.0 - (time_spread / max(self.coincidence_window_seconds, 1.0)))

        score = (
            0.35 * station_ratio
            + 0.30 * snr_score
            + 0.20 * sta_lta_score
            + 0.15 * coincidence_score
        )
        return clamp01(score)

    def _weighted_centroid(self, triggers: List[StationTrigger]) -> Tuple[float, float]:
        weights = [max(trigger.snr * trigger.sta_lta, 0.1) for trigger in triggers]
        weight_sum = sum(weights)
        latitude = sum(trigger.latitude * weight for trigger, weight in zip(triggers, weights)) / weight_sum
        longitude = sum(trigger.longitude * weight for trigger, weight in zip(triggers, weights)) / weight_sum
        return latitude, longitude

    @staticmethod
    def _coordinates_valid(latitude: float, longitude: float) -> bool:
        return isfinite(latitude) and isfinite(longitude) and -90.0 <= latitude <= 90.0 and -180.0 <= longitude <= 180.0


def rms(values: Iterable[float]) -> float:
    numbers = [float(value) for value in values]
    if not numbers:
        return 0.0
    return sqrt(sum(value * value for value in numbers) / len(numbers))


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def maximum_of_four(value: int) -> int:
    return max(4, int(value))
