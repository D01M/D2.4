/**
 * Location Search Panel System - Simple Working Version
 */

class LocationSearchPanel {
    static async init() {
        if (document.getElementById('locationSearchPanel')) return;

        const panel = document.createElement('div');
        panel.id = 'locationSearchPanel';
        panel.style.cssText = `
            position: fixed; top: 80px; left: 20px; width: 300px;
            background: #0b1627; border: 1px solid #1f334d; border-radius: 14px;
            padding: 14px; z-index: 1000; box-shadow: 0 10px 30px rgba(0,0,0,0.25);
            font-size: 12px; color: #e5eefc;
        `;

        panel.innerHTML = `
            <div style="margin-bottom: 12px;">
                <input type="text" id="locationSearchInput" placeholder="Search city, region, or coordinates..."
                    style="width: 100%; padding: 8px; background: #0f1d31; border: 1px solid #203653;
                    border-radius: 6px; color: #e5eefc; font-size: 12px;">
            </div>
            <div id="locationSearchResults" style="max-height: 300px; overflow-y: auto;"></div>
            <div id="locationInfo" style="background: #0f1d31; padding: 10px; border-radius: 6px; margin-top: 10px; display: none;"></div>
        `;

        document.body.appendChild(panel);

        const input = document.getElementById('locationSearchInput');
        input.addEventListener('input', (e) => this.search(e.target.value));
        input.addEventListener('change', (e) => this.selectLocation(e.target.value));
    }

    static async search(query) {
        if (!query) {
            document.getElementById('locationSearchResults').innerHTML = '';
            return;
        }

        try {
            const response = await fetch(`/api/location/search?query=${encodeURIComponent(query)}`);
            if (!response.ok) return;
            const data = await response.json();

            const results = data.search_results || [];
            let html = '';
            for (const r of results.slice(0, 5)) {
                html += `<div style="padding: 8px; background: #0f1d31; margin-bottom: 6px; border-radius: 4px; cursor: pointer;"
                    onclick="LocationSearchPanel.selectLocation('${r.name}')">${r.name}</div>`;
            }
            document.getElementById('locationSearchResults').innerHTML = html;
        } catch (err) {
            console.log('Search error:', err);
        }
    }

    static async selectLocation(name) {
        try {
            const response = await fetch(`/api/location/search?query=${encodeURIComponent(name)}`);
            if (!response.ok) return;
            const data = await response.json();
            const loc = data.search_results?.[0];
            if (!loc) return;

            const infoDiv = document.getElementById('locationInfo');
            infoDiv.innerHTML = `
                <div style="font-weight: bold; margin-bottom: 8px;">${loc.name}</div>
                <div style="font-size: 11px; color: #94a3b8;">
                    ${loc.country || ''}<br>
                    ${loc.latitude?.toFixed(3)}, ${loc.longitude?.toFixed(3)}<br>
                    Risk: ${loc.risk_level || 'Unknown'}
                </div>
            `;
            infoDiv.style.display = 'block';

            if (window.map && loc.latitude && loc.longitude) {
                window.map.setView([loc.latitude, loc.longitude], 6);
            }
        } catch (err) {
            console.log('Select error:', err);
        }
    }
}

// Auto-init when map is ready
if (typeof window !== 'undefined') {
    window.LocationSearchPanel = LocationSearchPanel;
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(() => LocationSearchPanel.init(), 500);
    });
}
