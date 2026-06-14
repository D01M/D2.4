/**
 * Live Alerts Control Panel
 * UI for managing earthquake alert preferences
 */

class AlertControlPanel {
    constructor() {
        this.container = null;
        this.isOpen = false;
    }
    
    /**
     * Create and insert control panel into the DOM
     */
    create() {
        const panel = document.createElement('div');
        panel.id = 'alert-control-panel';
        panel.innerHTML = `
            <style>
                #alert-control-panel {
                    position: fixed;
                    bottom: 20px;
                    right: 20px;
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 4px 16px rgba(0,0,0,0.2);
                    z-index: 9999;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                }
                
                #alert-control-panel.closed {
                    width: 60px;
                    height: 60px;
                }
                
                #alert-control-panel.open {
                    width: 320px;
                    max-height: 500px;
                    overflow-y: auto;
                }
                
                .alert-panel-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 16px;
                    border-bottom: 1px solid #e5e7eb;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border-radius: 8px 8px 0 0;
                    cursor: pointer;
                }
                
                #alert-toggle-btn {
                    width: 100%;
                    height: 100%;
                    border: none;
                    background: none;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 24px;
                    border-radius: 8px;
                }
                
                #alert-control-panel.closed .alert-panel-header {
                    height: 100%;
                    border-radius: 8px;
                }
                
                .alert-panel-title {
                    font-weight: 600;
                    font-size: 14px;
                }
                
                .alert-close-btn {
                    background: none;
                    border: none;
                    color: white;
                    font-size: 20px;
                    cursor: pointer;
                    padding: 0;
                }
                
                .alert-panel-content {
                    display: none;
                    padding: 16px;
                    max-height: 400px;
                    overflow-y: auto;
                }
                
                #alert-control-panel.open .alert-panel-content {
                    display: block;
                }
                
                .alert-section {
                    margin-bottom: 16px;
                }
                
                .alert-section-title {
                    font-weight: 600;
                    font-size: 12px;
                    text-transform: uppercase;
                    color: #6b7280;
                    margin-bottom: 8px;
                }
                
                .alert-toggle {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    margin-bottom: 8px;
                }
                
                .alert-toggle label {
                    font-size: 13px;
                    color: #374151;
                    cursor: pointer;
                }
                
                .toggle-switch {
                    position: relative;
                    width: 40px;
                    height: 20px;
                }
                
                .toggle-switch input {
                    opacity: 0;
                    width: 0;
                    height: 0;
                }
                
                .toggle-slider {
                    position: absolute;
                    cursor: pointer;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background-color: #ccc;
                    transition: 0.3s;
                    border-radius: 20px;
                }
                
                .toggle-slider:before {
                    position: absolute;
                    content: "";
                    height: 16px;
                    width: 16px;
                    left: 2px;
                    bottom: 2px;
                    background-color: white;
                    transition: 0.3s;
                    border-radius: 50%;
                }
                
                input:checked + .toggle-slider {
                    background-color: #667eea;
                }
                
                input:checked + .toggle-slider:before {
                    transform: translateX(20px);
                }
                
                .alert-slider {
                    width: 100%;
                    height: 5px;
                    margin: 8px 0;
                    background: #e5e7eb;
                    outline: none;
                    border-radius: 5px;
                    -webkit-appearance: none;
                }
                
                .alert-slider::-webkit-slider-thumb {
                    -webkit-appearance: none;
                    appearance: none;
                    width: 16px;
                    height: 16px;
                    background: #667eea;
                    cursor: pointer;
                    border-radius: 50%;
                }
                
                .alert-slider::-moz-range-thumb {
                    width: 16px;
                    height: 16px;
                    background: #667eea;
                    cursor: pointer;
                    border-radius: 50%;
                    border: none;
                }
                
                .alert-input-label {
                    font-size: 12px;
                    color: #6b7280;
                    margin-bottom: 4px;
                }
                
                .alert-input-value {
                    font-size: 13px;
                    font-weight: 600;
                    color: #667eea;
                    text-align: right;
                }
                
                .alert-button {
                    width: 100%;
                    padding: 8px 12px;
                    margin-top: 8px;
                    border: none;
                    border-radius: 4px;
                    background: #667eea;
                    color: white;
                    font-size: 12px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: 0.2s;
                }
                
                .alert-button:hover {
                    background: #5568d3;
                }
                
                .alert-button.secondary {
                    background: #e5e7eb;
                    color: #374151;
                }
                
                .alert-button.secondary:hover {
                    background: #d1d5db;
                }
                
                .alert-status {
                    font-size: 12px;
                    color: #6b7280;
                    padding: 8px;
                    background: #f3f4f6;
                    border-radius: 4px;
                    margin-top: 8px;
                }
                
                .alert-status.connected {
                    color: #059669;
                }
                
                .alert-status.disconnected {
                    color: #dc2626;
                }
            </style>
            
            <div class="alert-panel-header">
                <span class="alert-panel-title">🔔 Alerts</span>
                <button class="alert-close-btn" id="alert-panel-close">✕</button>
            </div>
            
            <div class="alert-panel-content">
                <!-- Sound Controls -->
                <div class="alert-section">
                    <div class="alert-section-title">Sound Alerts</div>
                    <div class="alert-toggle">
                        <label for="sound-enabled">Enable Sounds</label>
                        <label class="toggle-switch">
                            <input type="checkbox" id="sound-enabled" checked>
                            <span class="toggle-slider"></span>
                        </label>
                    </div>
                    
                    <div class="alert-input-label">Volume Level</div>
                    <div style="display: flex; gap: 8px;">
                        <input type="range" id="sound-volume" min="0" max="100" value="70" class="alert-slider" style="flex: 1;">
                        <div class="alert-input-value" id="volume-value">70%</div>
                    </div>
                </div>
                
                <!-- Notification Controls -->
                <div class="alert-section">
                    <div class="alert-section-title">Notifications</div>
                    <div class="alert-toggle">
                        <label for="notification-enabled">Enable Notifications</label>
                        <label class="toggle-switch">
                            <input type="checkbox" id="notification-enabled" checked>
                            <span class="toggle-slider"></span>
                        </label>
                    </div>
                </div>
                
                <!-- Vibration Controls -->
                <div class="alert-section">
                    <div class="alert-section-title">Vibration</div>
                    <div class="alert-toggle">
                        <label for="vibration-enabled">Enable Vibration</label>
                        <label class="toggle-switch">
                            <input type="checkbox" id="vibration-enabled" checked>
                            <span class="toggle-slider"></span>
                        </label>
                    </div>
                </div>
                
                <!-- Tsunami Alert Controls -->
                <div class="alert-section">
                    <div class="alert-section-title">🌊 Tsunami Alerts (Japanese Siren)</div>
                    <div class="alert-toggle">
                        <label for="tsunami-enabled">Enable Tsunami Alerts</label>
                        <label class="toggle-switch">
                            <input type="checkbox" id="tsunami-enabled" checked>
                            <span class="toggle-slider"></span>
                        </label>
                    </div>
                    <div style="font-size: 11px; color: #9ca3af; margin-top: 4px; line-height: 1.4;">
                        Japanese-style warning sirens for tsunami threats (M≥6.5 earthquakes only)
                    </div>
                </div>
                
                <!-- EEW Alert Controls -->
                <div class="alert-section">
                    <div class="alert-section-title">⚠️ EEW Alerts (Early Warning)</div>
                    <div class="alert-toggle">
                        <label for="eew-enabled">Enable EEW Alerts</label>
                        <label class="toggle-switch">
                            <input type="checkbox" id="eew-enabled" checked>
                            <span class="toggle-slider"></span>
                        </label>
                    </div>
                    <div style="font-size: 11px; color: #9ca3af; margin-top: 4px; line-height: 1.4;">
                        緊急地震速報 - Rapid beep alerts with 5-30s warning before shaking (M≥5.0 only)
                    </div>
                </div>
                
                <!-- Magnitude Threshold -->
                <div class="alert-section">
                    <div class="alert-section-title">Magnitude Threshold</div>
                    <div style="display: flex; gap: 8px;">
                        <input type="range" id="mag-threshold" min="3.0" max="7.0" step="0.1" value="4.5" class="alert-slider" style="flex: 1;">
                        <div class="alert-input-value" id="mag-value">4.5</div>
                    </div>
                </div>
                
                <!-- Auto-Mute Duration -->
                <div class="alert-section">
                    <div class="alert-section-title">Auto-Mute Duration</div>
                    <div style="display: flex; gap: 8px;">
                        <input type="range" id="auto-mute" min="0" max="300" step="10" value="60" class="alert-slider" style="flex: 1;">
                        <div class="alert-input-value" id="mute-value">60s</div>
                    </div>
                </div>
                
                <!-- Action Buttons -->
                <div class="alert-section">
                    <button class="alert-button" id="alert-mute-btn">🔇 Mute Alerts (60s)</button>
                    <button class="alert-button secondary" id="alert-reset-btn">Reset to Defaults</button>
                </div>
                
                <!-- Status -->
                <div class="alert-status connected" id="alert-status">
                    ✓ Connected to live stream
                </div>
            </div>
        `;
        
        document.body.appendChild(panel);
        this.container = panel;
        this.setupEventListeners();
        this.loadPreferences();
        this.closePanel();
    }
    
    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Toggle panel
        document.getElementById('alert-panel-close').addEventListener('click', () => this.togglePanel());
        
        // Header click to toggle
        document.querySelector('.alert-panel-header').addEventListener('click', () => this.togglePanel());
        
        // Sound controls
        document.getElementById('sound-enabled').addEventListener('change', (e) => {
            window.liveAlertSystem?.setPreferences({ sound_enabled: e.target.checked });
        });
        
        document.getElementById('sound-volume').addEventListener('input', (e) => {
            const val = parseInt(e.target.value);
            document.getElementById('volume-value').textContent = val + '%';
            window.liveAlertSystem?.setPreferences({ sound_volume: val / 100 });
        });
        
        // Notification
        document.getElementById('notification-enabled').addEventListener('change', (e) => {
            window.liveAlertSystem?.setPreferences({ notification_enabled: e.target.checked });
        });
        
        // Vibration
        document.getElementById('vibration-enabled').addEventListener('change', (e) => {
            window.liveAlertSystem?.setPreferences({ vibration_enabled: e.target.checked });
        });
        
        // Tsunami alerts
        document.getElementById('tsunami-enabled').addEventListener('change', (e) => {
            window.liveAlertSystem?.setPreferences({ tsunami_enabled: e.target.checked });
        });
        
        // EEW alerts
        document.getElementById('eew-enabled').addEventListener('change', (e) => {
            window.liveAlertSystem?.setPreferences({ eew_enabled: e.target.checked });
        });
        
        // Magnitude threshold
        document.getElementById('mag-threshold').addEventListener('input', (e) => {
            const val = parseFloat(e.target.value);
            document.getElementById('mag-value').textContent = val.toFixed(1);
            window.liveAlertSystem?.setPreferences({ min_magnitude_threshold: val });
        });
        
        // Auto-mute duration
        document.getElementById('auto-mute').addEventListener('input', (e) => {
            const val = parseInt(e.target.value);
            document.getElementById('mute-value').textContent = val + 's';
            window.liveAlertSystem?.setPreferences({ auto_mute_after_seconds: val });
        });
        
        // Buttons
        document.getElementById('alert-mute-btn').addEventListener('click', () => {
            const duration = parseInt(document.getElementById('auto-mute').value);
            window.liveAlertSystem?.toggleMute(duration);
        });
        
        document.getElementById('alert-reset-btn').addEventListener('click', () => {
            if (confirm('Reset all alert settings to defaults?')) {
                window.liveAlertSystem?.setPreferences(window.liveAlertSystem.getDefaultPreferences());
                this.loadPreferences();
            }
        });
    }
    
    /**
     * Load preferences and update UI
     */
    loadPreferences() {
        const prefs = window.liveAlertSystem?.preferences;
        if (!prefs) return;
        
        document.getElementById('sound-enabled').checked = prefs.sound_enabled;
        document.getElementById('sound-volume').value = Math.round(prefs.sound_volume * 100);
        document.getElementById('volume-value').textContent = Math.round(prefs.sound_volume * 100) + '%';
        
        document.getElementById('notification-enabled').checked = prefs.notification_enabled;
        document.getElementById('vibration-enabled').checked = prefs.vibration_enabled;
        document.getElementById('tsunami-enabled').checked = prefs.tsunami_enabled ?? true;
        document.getElementById('eew-enabled').checked = prefs.eew_enabled ?? true;
        
        document.getElementById('mag-threshold').value = prefs.min_magnitude_threshold;
        document.getElementById('mag-value').textContent = prefs.min_magnitude_threshold.toFixed(1);
        
        document.getElementById('auto-mute').value = prefs.auto_mute_after_seconds;
        document.getElementById('mute-value').textContent = prefs.auto_mute_after_seconds + 's';
    }
    
    /**
     * Toggle panel open/closed
     */
    togglePanel() {
        if (this.isOpen) {
            this.closePanel();
        } else {
            this.openPanel();
        }
    }
    
    /**
     * Open panel
     */
    openPanel() {
        this.container.classList.remove('closed');
        this.container.classList.add('open');
        this.isOpen = true;
    }
    
    /**
     * Close panel
     */
    closePanel() {
        this.container.classList.add('closed');
        this.container.classList.remove('open');
        this.isOpen = false;
    }
}

// Initialize control panel when live alerts are ready
window.addEventListener('load', () => {
    if (window.liveAlertSystem) {
        const panel = new AlertControlPanel();
        panel.create();
        window.alertControlPanel = panel;
    }
});
