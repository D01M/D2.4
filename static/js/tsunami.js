/**
 * Tsunami/Waves Module - Seismic wave visualization and animation
 */

let waveEntities = [];
let activeWaveAnimations = [];

/**
 * Clear all active wave animations
 */
function clearWaveAnimations() {
  activeWaveAnimations.forEach(a => {
    try {
      viewer.clock.onTick.removeEventListener(a.listener);
    } catch (_) {}
  });
  activeWaveAnimations = [];
  clearEntities(waveEntities);
}

/**
 * Draw seismic waves propagating from epicenter
 * @param {Object} ev - Event data with lat, lon, depth, mag, place, time
 */
function drawWaves(ev) {
  clearWaveAnimations();

  if (!ev || !document.getElementById("showWaves").checked) return;

  const mag = Math.max(1, ev.mag || 4);
  const maxRadius = Math.min(3000000, Math.max(450000, mag * 360000));
  const start = performance.now();
  const duration = 7500;

  const waves = [
    ["P", 0, 1.25, "#44aaff", 9000],
    ["S", 1100, 0.78, "#ffde59", 14000],
    ["Surface", 2100, 0.55, "#ff4d6d", 19000]
  ];

  waves.forEach(([name, delay, speed, css, height]) => {
    const color = Cesium.Color.fromCssColorString(css);

    const entity = viewer.entities.add({
      position: Cesium.Cartesian3.fromDegrees(ev.lon, ev.lat, height),
      ellipse: {
        semiMajorAxis: 1,
        semiMinorAxis: 1,
        material: color.withAlpha(0),
        outline: true,
        outlineColor: color.withAlpha(0),
        height
      }
    });

    waveEntities.push(entity);

    const listener = () => {
      const elapsed = performance.now() - start - delay;

      if (elapsed < 0) return;

      const t = Math.min(elapsed / duration, 1);
      const ease = 1 - Math.pow(1 - t, 2);
      const radius = Math.max(1, maxRadius * ease * speed);
      const alpha = Math.max(0, 0.7 * (1 - t));

      entity.ellipse.semiMajorAxis = radius;
      entity.ellipse.semiMinorAxis = radius;
      entity.ellipse.outlineColor = color.withAlpha(alpha);
      entity.ellipse.material = color.withAlpha(alpha * 0.08);

      if (t >= 1) {
        try {
          viewer.clock.onTick.removeEventListener(listener);
        } catch (_) {}
        try {
          viewer.entities.remove(entity);
        } catch (_) {}
        waveEntities = waveEntities.filter(x => x !== entity);
        activeWaveAnimations = activeWaveAnimations.filter(x => x.listener !== listener);
      }
    };

    viewer.clock.onTick.addEventListener(listener);
    activeWaveAnimations.push({ listener, entity });
  });
}

/**
 * Get all wave entities
 */
function getWaveEntities() {
  return waveEntities;
}
