/**
 * Map Module - Cesium viewer initialization and camera controls
 * Optimized for performance with lazy rendering and entity pooling
 */

let viewer;
let rotation = false;
let lastTick = Date.now();
let renderEnabled = false;

/**
 * Initialize the Cesium viewer with performance optimizations
 */
async function initMap() {
  try {
    PerformanceMonitor.markCesiumReady(); // Start timing

    Cesium.Ion.defaultAccessToken = "";
    
    // Create viewer with performance options
    viewer = new Cesium.Viewer("cesiumContainer", {
      animation: false,
      timeline: false,
      fullscreenButton: false,
      geocoder: false,
      sceneModePicker: false,
      baseLayerPicker: false,
      homeButton: false,
      navigationHelpButton: false,
      infoBox: false,
      selectionIndicator: false,
      terrainProvider: new Cesium.EllipsoidTerrainProvider(),
      imageryProvider: new Cesium.OpenStreetMapImageryProvider({
        url: "https://tile.openstreetmap.org/"
      }),
      // Performance: Use on-demand rendering instead of continuous
      requestRenderMode: true,
      maximumRenderTimeChange: 0.0
    });

    // Configure scene for optimal performance
    viewer.scene.globe.enableLighting = true;
    viewer.scene.globe.showGroundAtmosphere = true;
    viewer.scene.skyAtmosphere.show = true;
    viewer.scene.fog.enabled = false;
    viewer.scene.postProcessStages.fxaa.enabled = false;
    viewer.scene.postProcessStages.bloom.enabled = false;
    viewer.scene.backgroundColor = Cesium.Color.BLACK;

    // Advanced performance optimizations
    viewer.resolutionScale = 0.55; // Reduced resolution for better performance
    viewer.scene.screenSpaceCameraController.enableCollisionDetection = false;
    viewer.scene.screenSpaceCameraController.minimumZoomDistance = 1000000;
    viewer.scene.screenSpaceCameraController.maximumZoomDistance = 56000000;

    // Optimization: Batch rendering for better frame rates
    viewer.scene.preRender.addEventListener(() => {
      // Dynamic LOD adjustment based on zoom level
      const cameraHeight = Cesium.Cartesian3.distance(
        viewer.camera.position,
        Cesium.Cartesian3.fromDegrees(0, 0)
      );
      
      // Reduce detail when zoomed out
      if (cameraHeight > 20000000) {
        viewer.resolutionScale = 0.4;
      } else if (cameraHeight > 10000000) {
        viewer.resolutionScale = 0.5;
      } else {
        viewer.resolutionScale = 0.6;
      }
    });

    // Set initial camera view
    resetView();

    // Performance: Set up rotation ticker only when needed
    viewer.clock.onTick.addEventListener(() => {
      if (!rotation) return;
      const now = Date.now();
      const dt = (now - lastTick) / 1000;
      lastTick = now;
      viewer.scene.camera.rotate(Cesium.Cartesian3.UNIT_Z, -0.002 * dt);
      viewer.scene.requestRender(); // Request render when rotating
    });

    // Camera movement event - request renders during interaction
    viewer.scene.camera.changed.addEventListener(() => {
      viewer.scene.requestRender();
    });

    // Set up throttled click handler for entity selection
    const handleEntityClick = throttleRAF((click) => {
      const picked = viewer.scene.pick(click.position);
      if (Cesium.defined(picked) && picked.id && picked.id._telemetry) {
        document.getElementById("telemetry").innerHTML = picked.id._telemetry;
        if (picked.id._eventData) {
          selectedEventForWaves = picked.id._eventData;
          drawWaves(selectedEventForWaves);
        }
        viewer.scene.requestRender();
      }
    });

    viewer.screenSpaceEventHandler.setInputAction(handleEntityClick, Cesium.ScreenSpaceEventType.LEFT_CLICK);

    renderEnabled = true;
    
  } catch (e) {
    console.error(e);
    updateStatus("Boot failed: " + e.message, true);
  }
}

/**
 * Switch between globe visualization modes
 * @param {string} mode - "osm" for OpenStreetMap, "satellite" for satellite imagery, "dark" for minimal
 */
function setGlobeMode(mode) {
  viewer.imageryLayers.removeAll();
  
  if (mode === "osm") {
    viewer.imageryLayers.addImageryProvider(
      new Cesium.OpenStreetMapImageryProvider({
        url: "https://tile.openstreetmap.org/"
      })
    );
  } else if (mode === "satellite") {
    // Use USGS high resolution satellite imagery
    viewer.imageryLayers.addImageryProvider(
      new Cesium.UrlTemplateImageryProvider({
        url: "https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}",
        credit: "USGS"
      })
    );
  } else if (mode === "dark") {
    // Dark mode using CartoDB tiles
    viewer.imageryLayers.addImageryProvider(
      new Cesium.UrlTemplateImageryProvider({
        url: "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
        credit: "CartoDB"
      })
    );
  } else {
    // Default to OSM
    viewer.imageryLayers.addImageryProvider(
      new Cesium.OpenStreetMapImageryProvider({
        url: "https://tile.openstreetmap.org/"
      })
    );
  }
}

/**
 * Reset camera to default view
 */
function resetView() {
  viewer.camera.flyTo({
    destination: Cesium.Cartesian3.fromDegrees(44.8271, 28, 27000000),
    orientation: {
      heading: 0,
      pitch: -Cesium.Math.PI_OVER_TWO,
      roll: 0
    },
    duration: 1.1
  });
}

/**
 * Toggle globe auto-rotation
 */
function toggleRotation() {
  rotation = !rotation;
  lastTick = Date.now();
}

/**
 * Get the Cesium viewer instance
 */
function getViewer() {
  return viewer;
}

/**
 * Add a point entity to the map
 * @param {number} lon - Longitude
 * @param {number} lat - Latitude
 * @param {number} height - Height above ground
 * @param {number} size - Pixel size
 * @param {Cesium.Color} color - Color
 * @param {Cesium.Color} outline - Outline color
 * @param {string} telemetry - HTML telemetry content
 * @param {Array} arr - Array to store entity reference
 * @param {boolean} show - Visibility flag
 */
function addPoint(lon, lat, height, size, color, outline, telemetry, arr, show = true) {
  const e = viewer.entities.add({
    position: Cesium.Cartesian3.fromDegrees(lon, lat, height),
    point: {
      pixelSize: size,
      color,
      outlineColor: outline || Cesium.Color.WHITE,
      outlineWidth: 1,
      scaleByDistance: new Cesium.NearFarScalar(1.5e6, 1.2, 2.8e7, 0.35)
    },
    show
  });
  e._telemetry = telemetry;
  arr.push(e);
  return e;
}

/**
 * Add a ring entity to the map
 * @param {number} lon - Longitude
 * @param {number} lat - Latitude
 * @param {number} radiusKm - Radius in kilometers
 * @param {Cesium.Color} color - Color
 * @param {string} telemetry - HTML telemetry content
 * @param {Array} arr - Array to store entity reference
 * @param {boolean} show - Visibility flag
 */
function addRing(lon, lat, radiusKm, color, telemetry, arr, show = true) {
  const e = viewer.entities.add({
    position: Cesium.Cartesian3.fromDegrees(lon, lat, 3000),
    ellipse: {
      semiMajorAxis: radiusKm * 1000,
      semiMinorAxis: radiusKm * 1000,
      material: color.withAlpha(0.08),
      outline: true,
      outlineColor: color.withAlpha(0.55),
      height: 3000
    },
    show
  });
  e._telemetry = telemetry;
  arr.push(e);
  return e;
}
