#!/usr/bin/env python
"""Tests for the station metadata manager."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from openseismo.stations.station_manager import StationManager


class StationManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.station_file = Path(self.temp_dir.name) / "stations.json"
        current_time = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        payload = {
            "stations": [
                {
                    "id": "alpha",
                    "network": "AA",
                    "code": "A1",
                    "name": "Alpha",
                    "latitude": 10.0,
                    "longitude": 20.0,
                    "channels": ["BHZ", "BHN"],
                    "status": "online",
                    "priority": 3,
                    "tags": ["core", "land"],
                    "last_seen": current_time,
                    "noise_level": 12.5,
                    "country": "JP",
                    "region": "Tokyo",
                },
                {
                    "id": "alpha-dup",
                    "network": "AA",
                    "code": "A1",
                    "name": "Duplicate",
                    "latitude": 11.0,
                    "longitude": 21.0,
                    "channels": ["BHZ"],
                    "status": "online",
                },
                {
                    "id": "bad-coords",
                    "network": "BB",
                    "code": "B1",
                    "name": "Bad Coords",
                    "latitude": 200.0,
                    "longitude": 21.0,
                    "channels": ["BHZ"],
                    "status": "online",
                },
                {
                    "id": "missing-channels",
                    "network": "CC",
                    "code": "C1",
                    "name": "Missing Channels",
                    "latitude": 12.0,
                    "longitude": 22.0,
                    "channels": [],
                    "status": "online",
                },
                {
                    "id": "offline",
                    "network": "DD",
                    "code": "D1",
                    "name": "Offline",
                    "latitude": 13.0,
                    "longitude": 23.0,
                    "channels": ["BHZ"],
                    "status": "offline",
                    "tags": ["remote"],
                },
            ]
        }
        self.station_file.write_text(json.dumps(payload), encoding="utf-8")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_loads_valid_stations_and_skips_invalid_duplicates(self):
        manager = StationManager(self.station_file)

        stations = manager.list_stations()
        self.assertEqual(len(stations), 2)
        self.assertEqual(manager.get_station_by_network_code("AA", "A1")["id"], "alpha")
        self.assertIsNone(manager.get_station_by_network_code("BB", "B1"))
        self.assertIsNone(manager.get_station_by_network_code("CC", "C1"))

    def test_filters_by_status_channel_tag_and_recent_activity(self):
        manager = StationManager(self.station_file)

        self.assertEqual(len(manager.filter_stations(status="online")), 1)
        self.assertEqual(len(manager.filter_stations(channel="BHZ")), 2)
        self.assertEqual(len(manager.filter_stations(tag="core")), 1)
        self.assertEqual(len(manager.filter_stations(active_only=True)), 1)
        self.assertEqual(len(manager.filter_stations(recent_minutes=1)), 1)

    def test_updates_are_safe_and_unknown_stations_do_not_crash(self):
        manager = StationManager(self.station_file)

        self.assertEqual(manager.mark_offline("alpha")["status"], "offline")
        self.assertEqual(manager.mark_online("alpha")["status"], "online")
        self.assertEqual(manager.mark_delayed("alpha")["status"], "delayed")
        self.assertEqual(manager.update_noise_level("alpha", 33.5)["noise_level"], 33.5)
        self.assertIsNotNone(manager.update_last_seen("alpha", datetime.now(timezone.utc)))
        self.assertIsNone(manager.mark_online("missing"))
        self.assertIsNone(manager.update_noise_level("missing", "bad"))
        self.assertIsNone(manager.update_last_seen("missing", "bad"))

    def test_georgian_ies_station_codes_are_present_in_catalog(self):
        manager = StationManager(Path("data/stations/stations.json"))

        self.assertIsNotNone(manager.get_station_by_network_code("IES", "S186"))
        self.assertIsNotNone(manager.get_station_by_network_code("IES", "SC07"))
        self.assertIsNotNone(manager.get_station_by_network_code("IES", "EMLK"))


if __name__ == "__main__":
    unittest.main()