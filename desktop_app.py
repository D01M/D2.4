"""
OpenSeismo Lite - Desktop GUI Application
Native Windows desktop interface with PySimpleGUI
Runs Flask backend in background thread with live earthquake monitoring, alerts, and sound notifications
"""

import PySimpleGUI as sg
import threading
import requests
import json
import time
from datetime import datetime
from pathlib import Path
import sys
import os
import subprocess
import socket

# Configure PySimpleGUI theme
sg.theme('DarkBlue3')
sg.set_options(font=('Arial', 10))

# Global state
app_state = {
    'flask_process': None,
    'server_running': False,
    'earthquakes': [],
    'muted': False,
    'preferences': {
        'sound_enabled': True,
        'notification_enabled': True,
        'tsunami_enabled': True,
        'eew_enabled': True,
        'min_magnitude_threshold': 4.5,
        'sound_volume': 0.7,
    }
}

class FlaskServer:
    """Manages Flask server process"""
    
    @staticmethod
    def start():
        """Start Flask server in background"""
        try:
            app_state['flask_process'] = subprocess.Popen(
                [sys.executable, 'server.py'],
                cwd=os.path.dirname(os.path.abspath(__file__)),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
            )
            time.sleep(2)  # Wait for server to start
            app_state['server_running'] = True
            return True
        except Exception as e:
            print(f"Error starting Flask server: {e}")
            return False
    
    @staticmethod
    def stop():
        """Stop Flask server"""
        if app_state['flask_process']:
            try:
                app_state['flask_process'].terminate()
                app_state['flask_process'].wait(timeout=5)
            except:
                app_state['flask_process'].kill()
            app_state['server_running'] = False

class APIClient:
    """Handles API calls to Flask backend"""
    
    BASE_URL = 'http://localhost:5000/api'
    
    @staticmethod
    def get_earthquakes():
        """Fetch recent earthquakes"""
        try:
            response = requests.get(f'{APIClient.BASE_URL}/earthquakes', timeout=5)
            return response.json() if response.ok else []
        except:
            return []
    
    @staticmethod
    def get_sound_alerts_config():
        """Fetch sound alert configuration"""
        try:
            response = requests.get(f'{APIClient.BASE_URL}/sound-alerts/config', timeout=5)
            return response.json() if response.ok else {}
        except:
            return {}
    
    @staticmethod
    def get_tsunami_config():
        """Fetch tsunami alert configuration"""
        try:
            response = requests.get(f'{APIClient.BASE_URL}/tsunami-alerts/config', timeout=5)
            return response.json() if response.ok else {}
        except:
            return {}
    
    @staticmethod
    def get_eew_config():
        """Fetch EEW alert configuration"""
        try:
            response = requests.get(f'{APIClient.BASE_URL}/eew-alerts/config', timeout=5)
            return response.json() if response.ok else {}
        except:
            return {}
    
    @staticmethod
    def get_preferences():
        """Fetch user alert preferences"""
        try:
            response = requests.get(f'{APIClient.BASE_URL}/alerts/preferences', timeout=5)
            return response.json() if response.ok else app_state['preferences']
        except:
            return app_state['preferences']
    
    @staticmethod
    def set_preferences(prefs):
        """Save user preferences"""
        try:
            response = requests.post(f'{APIClient.BASE_URL}/alerts/preferences', json=prefs, timeout=5)
            return response.ok
        except:
            return False

class EarthquakeMonitor:
    """Monitors and displays earthquakes"""
    
    @staticmethod
    def format_earthquake(eq):
        """Format earthquake data for display"""
        mag = eq.get('magnitude', 0)
        depth = eq.get('depth', 0)
        lat = eq.get('latitude', 0)
        lon = eq.get('longitude', 0)
        time_str = eq.get('timestamp', '')
        location = eq.get('location', 'Unknown')
        
        return f"M{mag:.1f} - {location} | Depth: {depth:.0f}km | {time_str}"
    
    @staticmethod
    def get_alert_color(magnitude):
        """Get color for magnitude"""
        if magnitude >= 7.0:
            return '#FF0000'  # Red - Critical
        elif magnitude >= 6.0:
            return '#FF6600'  # Orange - High
        elif magnitude >= 5.0:
            return '#FFCC00'  # Yellow - Moderate
        else:
            return '#00CC00'  # Green - Low

def create_main_window():
    """Create main application window"""
    
    layout = [
        # Header
        [sg.Text('🌍 OpenSeismo Lite - Earthquake Monitor', font=('Arial', 16, 'bold'), text_color='#00CCFF')],
        [sg.Text('Real-time earthquake alerts with EEW, Tsunami, and Live notifications', font=('Arial', 9), text_color='#AAAAAA')],
        
        # Status bar
        [sg.Text('Status: ', font=('Arial', 10, 'bold')),
         sg.Text('Connecting...', key='STATUS', text_color='#FFCC00', font=('Arial', 10))],
        [sg.Text('Last Update: Never', key='LAST_UPDATE', text_color='#888888', font=('Arial', 9))],
        
        # Main earthquake list
        [sg.Listbox(values=[], size=(80, 15), key='EARTHQUAKE_LIST', 
                   background_color='#1a1a1a', text_color='#00FF00', 
                   enable_events=True, pad=(5, 5))],
        
        # Alert controls section
        [sg.Frame('Alert Controls', [
            [sg.Checkbox('🔊 Sound Alerts', default=True, key='SOUND_ENABLED', enable_events=True),
             sg.Checkbox('🔔 Notifications', default=True, key='NOTIF_ENABLED', enable_events=True),
             sg.Checkbox('🌊 Tsunami Alerts', default=True, key='TSUNAMI_ENABLED', enable_events=True),
             sg.Checkbox('⚡ EEW Alerts', default=True, key='EEW_ENABLED', enable_events=True)],
            
            [sg.Text('Min Magnitude:', font=('Arial', 9)),
             sg.Slider(range=(3.0, 7.0), default_value=4.5, resolution=0.1, 
                      orientation='h', size=(20, 15), key='MAG_THRESHOLD', enable_events=True),
             sg.Text('Volume:', font=('Arial', 9)),
             sg.Slider(range=(0, 100), default_value=70, resolution=5, 
                      orientation='h', size=(15, 15), key='VOLUME', enable_events=True, suffix='%')],
            
            [sg.Button('🔇 Mute (60s)', key='MUTE_BTN', size=(12, 1)),
             sg.Button('📊 Refresh', key='REFRESH_BTN', size=(12, 1)),
             sg.Button('⚙️ Preferences', key='PREFS_BTN', size=(12, 1)),
             sg.Button('❌ Exit', key='EXIT_BTN', size=(12, 1))],
        ], font=('Arial', 10), pad=(5, 5))],
        
        # Auto-update checkbox
        [sg.Checkbox('🔄 Auto-update every 10 seconds', default=True, key='AUTO_UPDATE', enable_events=True)],
    ]
    
    window = sg.Window('OpenSeismo Lite - Desktop Application', layout, 
                       size=(900, 700), finalize=True, icon=None)
    
    return window

def update_earthquakes(window):
    """Fetch and update earthquake list"""
    try:
        earthquakes = APIClient.get_earthquakes()
        app_state['earthquakes'] = earthquakes
        
        # Filter by magnitude threshold
        threshold = app_state['preferences'].get('min_magnitude_threshold', 4.5)
        filtered = [eq for eq in earthquakes if eq.get('magnitude', 0) >= threshold]
        
        # Sort by magnitude (descending)
        filtered.sort(key=lambda x: x.get('magnitude', 0), reverse=True)
        
        # Format for display
        display_list = [EarthquakeMonitor.format_earthquake(eq) for eq in filtered[:100]]
        
        window['EARTHQUAKE_LIST'].update(values=display_list)
        window['LAST_UPDATE'].update(f'Last Update: {datetime.now().strftime("%H:%M:%S")}')
        
        if not app_state['server_running']:
            window['STATUS'].update('❌ Server Offline', text_color='#FF0000')
        elif filtered:
            window['STATUS'].update(f'✓ Online | {len(filtered)} earthquakes detected', text_color='#00FF00')
        else:
            window['STATUS'].update('✓ Online | Monitoring...', text_color='#00FF00')
            
    except Exception as e:
        window['STATUS'].update(f'⚠ Error: {str(e)[:30]}', text_color='#FF6600')

def update_monitor_loop(window, update_interval=10):
    """Background thread for auto-updating"""
    while True:
        try:
            if app_state.get('monitor_running', False):
                update_earthquakes(window)
            time.sleep(update_interval)
        except:
            time.sleep(5)

def main():
    """Main application loop"""
    
    print("[INFO] Starting OpenSeismo Lite Desktop Application...")
    
    # Start Flask server
    if not FlaskServer.start():
        sg.popup_error('Failed to start Flask server', title='Startup Error')
        return
    
    time.sleep(1)
    
    # Load preferences
    app_state['preferences'] = APIClient.get_preferences()
    
    # Create window
    window = create_main_window()
    
    # Start background update thread
    app_state['monitor_running'] = True
    monitor_thread = threading.Thread(target=update_monitor_loop, args=(window, 10), daemon=True)
    monitor_thread.start()
    
    # Initial update
    update_earthquakes(window)
    
    print("[INFO] Application started. Window opened.")
    
    # Event loop
    while True:
        event, values = window.read(timeout=1000)
        
        if event == sg.WINDOW_CLOSED or event == 'EXIT_BTN':
            break
        
        elif event == 'REFRESH_BTN':
            update_earthquakes(window)
        
        elif event == 'MUTE_BTN':
            app_state['muted'] = not app_state['muted']
            if app_state['muted']:
                window['MUTE_BTN'].update('🔊 Unmute')
                window['STATUS'].update('🔇 Alerts Muted', text_color='#FFCC00')
            else:
                window['MUTE_BTN'].update('🔇 Mute (60s)')
                window['STATUS'].update('✓ Online', text_color='#00FF00')
        
        elif event == 'SOUND_ENABLED':
            app_state['preferences']['sound_enabled'] = values['SOUND_ENABLED']
            APIClient.set_preferences(app_state['preferences'])
        
        elif event == 'NOTIF_ENABLED':
            app_state['preferences']['notification_enabled'] = values['NOTIF_ENABLED']
            APIClient.set_preferences(app_state['preferences'])
        
        elif event == 'TSUNAMI_ENABLED':
            app_state['preferences']['tsunami_enabled'] = values['TSUNAMI_ENABLED']
            APIClient.set_preferences(app_state['preferences'])
        
        elif event == 'EEW_ENABLED':
            app_state['preferences']['eew_enabled'] = values['EEW_ENABLED']
            APIClient.set_preferences(app_state['preferences'])
        
        elif event == 'MAG_THRESHOLD':
            app_state['preferences']['min_magnitude_threshold'] = values['MAG_THRESHOLD']
            APIClient.set_preferences(app_state['preferences'])
            update_earthquakes(window)
        
        elif event == 'VOLUME':
            app_state['preferences']['sound_volume'] = values['VOLUME'] / 100
            APIClient.set_preferences(app_state['preferences'])
        
        elif event == 'AUTO_UPDATE':
            app_state['monitor_running'] = values['AUTO_UPDATE']
            if app_state['monitor_running']:
                window['STATUS'].update('🔄 Auto-update enabled', text_color='#00FF00')
            else:
                window['STATUS'].update('⏸ Auto-update paused', text_color='#FFCC00')
    
    # Cleanup
    print("[INFO] Shutting down...")
    app_state['monitor_running'] = False
    FlaskServer.stop()
    window.close()
    print("[INFO] Application closed.")

if __name__ == '__main__':
    main()
