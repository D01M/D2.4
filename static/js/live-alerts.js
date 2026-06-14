/**
 * Live Earthquake Alerts System
 * Handles real-time updates, sound alerts, and browser notifications
 */

class LiveAlertSystem {
    constructor() {
        this.soundAlerts = {};
        this.tsunamiAlerts = {};
        this.eewAlerts = {};
        this.audioContext = null;
        this.preferences = this.getPreferences();
        this.eventSource = null;
        this.lastEarthquakeTime = new Date();
        this.isInitialized = false;
        this.muteUntil = null;
        
        this.init();
    }
    
    /**
     * Initialize the alert system
     */
    async init() {
        try {
            // Request notification permission
            if ('Notification' in window && Notification.permission === 'default') {
                await Notification.requestPermission();
            }
            
            // Initialize Web Audio API context (required for sounds)
            if (!this.audioContext && (window.AudioContext || window.webkitAudioContext)) {
                this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            }
            
            // Load sound configuration from server
            await this.loadSoundAlerts();
            
            // Connect to live update stream
            this.connectToLiveStream();
            
            this.isInitialized = true;
            console.log('✓ Live Alert System initialized');
        } catch (err) {
            console.error('Failed to initialize alert system:', err);
        }
    }
    
    /**
     * Load sound alert configuration from server
     */
    async loadSoundAlerts() {
        try {
            const soundResponse = await fetch('/api/sound-alerts/config');
            const soundData = await soundResponse.json();
            this.soundAlerts = soundData.sound_alerts;
            console.log('Sound alerts loaded:', Object.keys(this.soundAlerts));
            
            // Load tsunami alert configuration
            const tsunamiResponse = await fetch('/api/tsunami-alerts/config');
            const tsunamiData = await tsunamiResponse.json();
            this.tsunamiAlerts = tsunamiData.tsunami_alerts;
            console.log('Tsunami alerts loaded:', Object.keys(this.tsunamiAlerts));
            
            // Load EEW alert configuration
            const eewResponse = await fetch('/api/eew-alerts/config');
            const eewData = await eewResponse.json();
            this.eewAlerts = eewData.eew_alerts;
            console.log('EEW alerts loaded:', Object.keys(this.eewAlerts));
        } catch (err) {
            console.error('Failed to load alert configurations:', err);
        }
    }
    
    /**
     * Connect to Server-Sent Events stream for live updates
     */
    connectToLiveStream() {
        try {
            this.eventSource = new EventSource('/api/live-earthquakes/stream');
            
            this.eventSource.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    
                    if (data.type === 'new_earthquake') {
                        this.handleNewEarthquake(data.earthquake, data.alert, data.tsunami, data.eew);
                    } else if (data.type === 'update') {
                        this.handleEarthquakeUpdate(data.earthquake);
                    } else if (data.type === 'error') {
                        console.error('Stream error:', data.error);
                    }
                } catch (err) {
                    console.error('Error processing stream data:', err);
                }
            };
            
            this.eventSource.onerror = (err) => {
                console.error('EventSource error:', err);
                this.eventSource.close();
                // Reconnect after 10 seconds
                setTimeout(() => this.connectToLiveStream(), 10000);
            };
            
            console.log('Connected to live earthquake stream');
        } catch (err) {
            console.error('Failed to connect to live stream:', err);
        }
    }
    
    /**
     * Handle new earthquake detection
     */
    async handleNewEarthquake(earthquake, alertConfig, tsunamiWarning, eewWarning) {
        console.log('🔴 New earthquake detected:', earthquake);
        
        // Check if should mute
        if (this.isMuted()) {
            console.log('Alerts muted until:', this.muteUntil);
            return;
        }
        
        // Check magnitude threshold
        if (earthquake.magnitude < this.preferences.min_magnitude_threshold) {
            return;
        }
        
        // Play sound alert
        if (this.preferences.sound_enabled && alertConfig.sound) {
            this.playAlert(alertConfig.sound, this.preferences.sound_volume);
        }
        
        // Handle EEW if present (M5.0+) - plays BEFORE tsunami siren
        if (eewWarning && eewWarning.level && this.preferences.eew_enabled) {
            console.log('⚠️ EARTHQUAKE EARLY WARNING:', eewWarning);
            if (this.preferences.sound_enabled) {
                this.playEEWAlert(eewWarning, this.preferences.sound_volume);
            }
            if (this.preferences.notification_enabled) {
                this.showEEWNotification(eewWarning, earthquake);
            }
        }
        
        // Handle tsunami warning if present
        if (tsunamiWarning && tsunamiWarning.level && this.preferences.tsunami_enabled) {
            console.log('🌊 TSUNAMI WARNING:', tsunamiWarning);
            if (this.preferences.sound_enabled) {
                this.playTsunamiSiren(tsunamiWarning, this.preferences.sound_volume);
            }
            if (this.preferences.notification_enabled) {
                this.showTsunamiNotification(tsunamiWarning, earthquake);
            }
        }
        
        // Show browser notification for earthquake
        if (this.preferences.notification_enabled && alertConfig.notification) {
            this.showNotification(alertConfig.notification, earthquake);
        }
        
        // Trigger vibration (if supported and enabled)
        if (this.preferences.vibration_enabled && 'vibrate' in navigator) {
            this.vibrateAlert(alertConfig.level);
        }
        
        // Auto-mute after configured time
        if (this.preferences.auto_mute_after_seconds > 0) {
            this.setAutoMute(this.preferences.auto_mute_after_seconds);
        }
        
        this.lastEarthquakeTime = new Date();
    }
    
    /**
     * Handle earthquake data updates
     */
    handleEarthquakeUpdate(earthquake) {
        console.log('📊 Earthquake updated:', earthquake);
        // Could trigger additional alerts for intensity updates or tsunami warnings
    }
    
    /**
     * Play sound alert using Web Audio API
     */
    playAlert(soundConfig, volume = 0.7) {
        if (!this.audioContext) {
            console.warn('Web Audio API not available');
            return;
        }
        
        try {
            const ctx = this.audioContext;
            const now = ctx.currentTime;
            const duration = soundConfig.duration_ms / 1000;
            
            // Create oscillator for tone
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            
            osc.connect(gain);
            gain.connect(ctx.destination);
            
            osc.frequency.value = soundConfig.frequency;
            osc.type = soundConfig.type || 'sine';
            
            // Set volume envelope (fade in/out)
            gain.gain.setValueAtTime(0, now);
            gain.gain.linearRampToValueAtTime(volume, now + 0.1);
            gain.gain.linearRampToValueAtTime(0, now + duration);
            
            osc.start(now);
            osc.stop(now + duration);
            
            console.log(`🔊 Alert played: ${soundConfig.frequency}Hz for ${soundConfig.duration_ms}ms`);
        } catch (err) {
            console.error('Failed to play alert:', err);
        }
    }
    
    /**
     * Play tsunami siren using frequency sweep (Japanese-style warning)
     */
    playTsunamiSiren(tsunamiWarning, volume = 1.0) {
        if (!this.audioContext) {
            console.warn('Web Audio API not available for tsunami siren');
            return;
        }
        
        try {
            const siren = tsunamiWarning.sound;
            if (!siren) return;
            
            const ctx = this.audioContext;
            const now = ctx.currentTime;
            const totalDuration = siren.duration_ms / 1000;
            const cycleDuration = totalDuration / siren.cycles;
            
            for (let cycle = 0; cycle < siren.cycles; cycle++) {
                const cycleStart = now + (cycle * cycleDuration);
                
                // Create oscillator for siren sweep
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                
                osc.connect(gain);
                gain.connect(ctx.destination);
                
                // Frequency sweep: up then down
                const sweepUpTime = cycleStart + (cycleDuration * 0.4);
                const peakTime = cycleStart + (cycleDuration * 0.5);
                const cycleEnd = cycleStart + cycleDuration;
                
                osc.frequency.setValueAtTime(siren.frequency_start, cycleStart);
                osc.frequency.linearRampToValueAtTime(siren.frequency_end, sweepUpTime);
                osc.frequency.linearRampToValueAtTime(siren.frequency_start, cycleEnd);
                
                // Volume envelope for each cycle
                gain.gain.setValueAtTime(0, cycleStart);
                gain.gain.linearRampToValueAtTime(volume, cycleStart + 0.05);
                gain.gain.linearRampToValueAtTime(volume, cycleEnd - 0.05);
                gain.gain.linearRampToValueAtTime(0, cycleEnd);
                
                osc.type = 'sine';
                osc.start(cycleStart);
                osc.stop(cycleEnd);
            }
            
            console.log(`🌊 Tsunami siren played: ${siren.label} - ${siren.description}`);
        } catch (err) {
            console.error('Failed to play tsunami siren:', err);
        }
    }
    
    /**
     * Show browser notification
     */
    showNotification(notification, earthquake) {
        if (!('Notification' in window)) {
            console.warn('Notifications not supported');
            return;
        }
        
        if (Notification.permission !== 'granted') {
            console.warn('Notification permission not granted');
            return;
        }
        
        try {
            const n = new Notification(notification.title, {
                body: notification.body,
                icon: notification.icon,
                badge: notification.badge,
                tag: notification.tag,
                requireInteraction: notification.requireInteraction,
                data: {
                    earthquake: earthquake
                }
            });
            
            n.onclick = () => {
                window.focus();
                window.open(`https://earthquake.usgs.gov/earthquakes/events/${earthquake.id}/`, '_blank');
                n.close();
            };
            
            console.log('📢 Notification shown:', notification.title);
        } catch (err) {
            console.error('Failed to show notification:', err);
        }
    }
    
    /**
     * Show tsunami warning notification
     */
    showTsunamiNotification(tsunamiWarning, earthquake) {
        if (!('Notification' in window) || Notification.permission !== 'granted') {
            return;
        }
        
        try {
            const levelEmojis = {
                'major_warning': '🌊🌊🌊',
                'warning': '🌊🌊',
                'advisory': '🌊'
            };
            
            const emoji = levelEmojis[tsunamiWarning.level] || '🌊';
            
            const n = new Notification(`${emoji} ${tsunamiWarning.sound.label}`, {
                body: `Wave Height: ${tsunamiWarning.wave_height_m}m | Region: ${tsunamiWarning.region || 'Unknown'} | Arrival: ${tsunamiWarning.arrival_minutes || '?'} min`,
                icon: '/static/tsunami-icon.png',
                badge: '/static/tsunami-badge.png',
                tag: 'tsunami-alert',
                requireInteraction: true,
                data: {
                    earthquake: earthquake,
                    tsunami: tsunamiWarning
                }
            });
            
            n.onclick = () => {
                window.focus();
                n.close();
            };
            
            console.log(`📢 Tsunami notification shown: ${tsunamiWarning.sound.label}`);
        } catch (err) {
            console.error('Failed to show tsunami notification:', err);
        }
    }
    
    /**
     * Play EEW (Earthquake Early Warning) alert - rapid beep sequence
     */
    playEEWAlert(eewWarning, volume = 1.0) {
        if (!this.audioContext) {
            console.warn('Web Audio API not available for EEW alert');
            return;
        }
        
        try {
            const eewConfig = eewWarning.sound;
            if (!eewConfig) return;
            
            const ctx = this.audioContext;
            const now = ctx.currentTime;
            const beepDuration = eewConfig.beep_duration_ms / 1000;
            const interval = eewConfig.interval_ms / 1000;
            
            for (let i = 0; i < eewConfig.beep_count; i++) {
                const startTime = now + (i * interval);
                
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                
                osc.connect(gain);
                gain.connect(ctx.destination);
                
                osc.frequency.value = eewConfig.frequency;
                osc.type = 'sine';
                
                // Volume envelope for each beep
                gain.gain.setValueAtTime(0, startTime);
                gain.gain.linearRampToValueAtTime(volume, startTime + 0.02);
                gain.gain.linearRampToValueAtTime(volume, startTime + beepDuration - 0.02);
                gain.gain.linearRampToValueAtTime(0, startTime + beepDuration);
                
                osc.start(startTime);
                osc.stop(startTime + beepDuration);
            }
            
            console.log(`⚠️ EEW Alert played: ${eewConfig.beep_count} beeps at ${eewConfig.frequency}Hz`);
        } catch (err) {
            console.error('Failed to play EEW alert:', err);
        }
    }
    
    /**
     * Show EEW notification with wave arrival times
     */
    showEEWNotification(eewWarning, earthquake) {
        if (!('Notification' in window) || Notification.permission !== 'granted') {
            return;
        }
        
        try {
            // Find nearest city with shortest countdown
            let nearest = null;
            let minCountdown = Infinity;
            
            if (eewWarning.arrivals) {
                for (const [city, data] of Object.entries(eewWarning.arrivals)) {
                    if (data.countdown < minCountdown) {
                        minCountdown = data.countdown;
                        nearest = { name: city, ...data };
                    }
                }
            }
            
            const bodyText = nearest 
                ? `⚡ Shaking in ${nearest.countdown}s | ${nearest.name} ${nearest.distance}`
                : `M${eewWarning.magnitude} - Strong shaking expected`;
            
            const n = new Notification(`⚠️ ${eewWarning.label}`, {
                body: bodyText,
                icon: '/static/eew-icon.png',
                badge: '/static/eew-badge.png',
                tag: 'eew-alert',
                requireInteraction: true,
                data: { earthquake, eew: eewWarning }
            });
            
            n.onclick = () => { window.focus(); n.close(); };
            console.log(`📢 EEW: ${eewWarning.label}`);
        } catch (err) {
            console.error('EEW notification failed:', err);
        }
    }
    
    
    /**
     * Trigger vibration pattern based on alert level
     */
    vibrateAlert(alertLevel) {
        if (!('vibrate' in navigator)) return;
        
        const patterns = {
            'low': [100],
            'moderate': [100, 100, 100],
            'high': [150, 100, 150, 100, 150],
            'critical': [200, 100, 200, 100, 200, 100, 200]
        };
        
        const pattern = patterns[alertLevel] || [100];
        navigator.vibrate(pattern);
    }
    
    /**
     * Mute alerts for a duration
     */
    setAutoMute(seconds) {
        this.muteUntil = new Date(Date.now() + seconds * 1000);
        console.log(`🔇 Alerts muted for ${seconds}s`);
        
        // Show visual indicator
        this.showMuteIndicator(seconds);
    }
    
    /**
     * Check if alerts are currently muted
     */
    isMuted() {
        return this.muteUntil && new Date() < this.muteUntil;
    }
    
    /**
     * Show visual mute indicator
     */
    showMuteIndicator(seconds) {
        let elem = document.getElementById('mute-indicator');
        if (!elem) {
            elem = document.createElement('div');
            elem.id = 'mute-indicator';
            elem.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: #ff9800;
                color: white;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 12px;
                z-index: 10000;
                box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            `;
            document.body.appendChild(elem);
        }
        
        elem.textContent = `🔇 Alerts muted (${seconds}s)`;
        elem.style.display = 'block';
        
        setTimeout(() => {
            elem.style.display = 'none';
            this.muteUntil = null;
        }, seconds * 1000);
    }
    
    /**
     * Get user preferences from localStorage
     */
    getPreferences() {
        try {
            const saved = localStorage.getItem('earthquake_alert_prefs');
            return saved ? JSON.parse(saved) : this.getDefaultPreferences();
        } catch (err) {
            return this.getDefaultPreferences();
        }
    }
    
    /**
     * Default alert preferences
     */
    getDefaultPreferences() {
        return {
            sound_enabled: true,
            notification_enabled: true,
            min_magnitude_threshold: 4.5,
            alert_levels: ['low', 'moderate', 'high', 'critical'],
            sound_volume: 0.7,
            auto_mute_after_seconds: 60,
            vibration_enabled: true,
            tsunami_enabled: true,
            eew_enabled: true,
            region_filter: null
        };
    }
    
    /**
     * Update alert preferences
     */
    setPreferences(prefs) {
        this.preferences = { ...this.preferences, ...prefs };
        try {
            localStorage.setItem('earthquake_alert_prefs', JSON.stringify(this.preferences));
            console.log('Preferences saved');
            
            // Send to server
            fetch('/api/alerts/preferences', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(this.preferences)
            });
        } catch (err) {
            console.error('Failed to save preferences:', err);
        }
    }
    
    /**
     * Manually mute/unmute alerts
     */
    toggleMute(duration = 60) {
        if (this.isMuted()) {
            this.muteUntil = null;
            console.log('Alerts unmuted');
        } else {
            this.setAutoMute(duration);
        }
    }
    
    /**
     * Disconnect from live stream
     */
    disconnect() {
        if (this.eventSource) {
            this.eventSource.close();
            console.log('Disconnected from live stream');
        }
    }
}

// Initialize on page load
window.liveAlertSystem = null;

function initLiveAlerts() {
    if (!window.liveAlertSystem) {
        window.liveAlertSystem = new LiveAlertSystem();
    }
    return window.liveAlertSystem;
}

// Auto-initialize if DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initLiveAlerts);
} else {
    initLiveAlerts();
}

// Expose controls globally
window.earthquake_alerts = {
    init: initLiveAlerts,
    toggleMute: (duration) => window.liveAlertSystem?.toggleMute(duration),
    setPreferences: (prefs) => window.liveAlertSystem?.setPreferences(prefs),
    getPreferences: () => window.liveAlertSystem?.preferences,
    disconnect: () => window.liveAlertSystem?.disconnect()
};
