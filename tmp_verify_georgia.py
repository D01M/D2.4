from pathlib import Path
from openseismo.stations.station_manager import StationManager

manager = StationManager(Path('data/stations/stations.json'))
for code in ['S186', 'SC07', 'EMLK']:
    entry = manager.get_station_by_network_code('IES', code)
    print(code, '->', entry['name'] if entry else None)
