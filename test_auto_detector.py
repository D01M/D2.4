#!/usr/bin/env python
"""Basic tests for the automatic earthquake detector."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from openseismo.detection.auto_detector import AutoEarthquakeDetector
from openseismo.stations.station_manager import StationManager


class AutoDetectorTests(unittest.TestCase):
    def setUp(self):
        self.detector = AutoEarthquakeDetector(
            minimum_station_count=4,
            coincidence_window_seconds=6.0,
            cooldown_seconds=30.0,
            min_snr=2.0,
            min_sta_lta=2.0,
            sta_window_seconds=0.5,
            lta_window_seconds=2.0,
        )
        self.stations = [
            ("STA01", 35.0, 139.0, "Station 1"),
            ("STA02", 35.2, 139.2, "Station 2"),
            ("STA03", 35.4, 139.4, "Station 3"),
            ("STA04", 35.6, 139.6, "Station 4"),
        ]
        for station_id, latitude, longitude, name in self.stations:
            self.detector.register_station(station_id, latitude, longitude, name, sample_rate_hz=10.0)

    def _feed_noise(self, station_id, start_time, count=40):
        samples = [0.05] * count
        timestamps = [start_time + timedelta(seconds=index * 0.1) for index in range(count)]
        return self.detector.add_samples_batch(station_id, samples, timestamps)

    def _feed_trigger(self, station_id, start_time):
        samples = [0.05] * 30 + [3.0] * 10
        timestamps = [start_time + timedelta(seconds=index * 0.1) for index in range(len(samples))]
        return self.detector.add_samples_batch(station_id, samples, timestamps)

    def test_no_trigger_from_noise(self):
        start = datetime.now(timezone.utc)
        events = self._feed_noise("STA01", start)
        self.assertEqual(events, [])

    def test_no_event_from_one_station(self):
        start = datetime.now(timezone.utc)
        events = self._feed_trigger("STA01", start)
        self.assertEqual(events, [])

    def test_event_requires_four_stations(self):
        start = datetime.now(timezone.utc)
        event_lists = []
        for offset, station_id in enumerate(["STA01", "STA02", "STA03", "STA04"]):
            event_lists.append(self._feed_trigger(station_id, start + timedelta(seconds=offset * 0.5)))

        events = [event for batch in event_lists for event in batch]
        self.assertTrue(events)
        event = events[-1]
        self.assertEqual(event.status, "automatic")
        self.assertGreaterEqual(len(event.triggers), 4)
        self.assertTrue(0.0 <= event.confidence <= 1.0)

    def test_cooldown_prevents_duplicates(self):
        start = datetime.now(timezone.utc)
        self._feed_trigger("STA01", start)
        self._feed_trigger("STA02", start + timedelta(seconds=0.5))
        self._feed_trigger("STA03", start + timedelta(seconds=1.0))
        first = self._feed_trigger("STA04", start + timedelta(seconds=1.5))
        self.assertTrue(first)

        second = self._feed_trigger("STA01", start + timedelta(seconds=2.0))
        self.assertEqual(second, [])

    def test_confidence_is_clamped(self):
        start = datetime.now(timezone.utc)
        self._feed_trigger("STA01", start)
        self._feed_trigger("STA02", start + timedelta(seconds=0.5))
        self._feed_trigger("STA03", start + timedelta(seconds=1.0))
        events = self._feed_trigger("STA04", start + timedelta(seconds=1.5))
        self.assertTrue(events)
        self.assertGreaterEqual(events[-1].confidence, 0.0)
        self.assertLessEqual(events[-1].confidence, 1.0)

        def test_sync_from_station_manager_skips_offline_by_default(self):
                with TemporaryDirectory() as temp_dir:
                        station_file = Path(temp_dir) / "stations.json"
                        station_file.write_text(
                                """
                                {
                                    "stations": [
                                        {"id": "a", "network": "AA", "code": "A1", "name": "Alpha", "latitude": 10.0, "longitude": 20.0, "channels": ["BHZ"], "status": "online"},
                                        {"id": "b", "network": "BB", "code": "B1", "name": "Beta", "latitude": 11.0, "longitude": 21.0, "channels": ["BHZ"], "status": "offline"}
                                    ]
                                }
                                """,
                                encoding="utf-8",
                        )

                        manager = StationManager(station_file)
                        detector = AutoEarthquakeDetector()

                        count = detector.sync_from_station_manager(manager)

                        self.assertEqual(count, 1)
                        self.assertEqual(detector.get_registered_station_ids(), ["a"])

                        detector.sync_from_station_manager(manager, include_offline=True)
                        self.assertEqual(detector.get_registered_station_ids(), ["a", "b"])


if __name__ == "__main__":
    unittest.main()