/**
 * Performance Module - Client-side optimization and monitoring
 * Handles resource caching, lazy loading, and performance tracking
 */

/**
 * Performance monitoring and metrics collection
 */
const PerformanceMonitor = {
  metrics: {
    pageLoadTime: 0,
    cesiumInitTime: 0,
    firstDataLoadTime: 0,
    apiCallTimes: [],
    frameRates: []
  },

  /**
   * Mark page load completion
   */
  markPageLoadComplete() {
    this.metrics.pageLoadTime = performance.now();
    console.log(`🚀 Page loaded in ${this.metrics.pageLoadTime.toFixed(0)}ms`);
  },

  /**
   * Mark Cesium initialization complete
   */
  markCesiumReady() {
    this.metrics.cesiumInitTime = performance.now();
    console.log(`🌍 Cesium ready in ${this.metrics.cesiumInitTime.toFixed(0)}ms`);
  },

  /**
   * Track API call performance
   * @param {string} endpoint - API endpoint called
   * @param {number} duration - Time in milliseconds
   */
  trackApiCall(endpoint, duration) {
    this.metrics.apiCallTimes.push({ endpoint, duration, time: new Date() });
    if (this.metrics.apiCallTimes.length > 100) {
      this.metrics.apiCallTimes.shift(); // Keep last 100 calls
    }
  },

  /**
   * Get performance report
   */
  getReport() {
    const avgApiTime = this.metrics.apiCallTimes.length > 0
      ? (this.metrics.apiCallTimes.reduce((sum, c) => sum + c.duration, 0) / this.metrics.apiCallTimes.length).toFixed(0)
      : 0;

    return {
      pageLoadTime: `${this.metrics.pageLoadTime.toFixed(0)}ms`,
      cesiumInitTime: `${this.metrics.cesiumInitTime.toFixed(0)}ms`,
      avgApiCallTime: `${avgApiTime}ms`,
      totalApiCalls: this.metrics.apiCallTimes.length
    };
  }
};

/**
 * Local storage cache with TTL support
 */
const CacheManager = {
  prefix: 'osm_cache_',
  defaultTTL: 5 * 60 * 1000, // 5 minutes

  /**
   * Get cached data
   * @param {string} key - Cache key
   * @returns {any|null} Cached data or null if expired/missing
   */
  get(key) {
    try {
      const item = localStorage.getItem(this.prefix + key);
      if (!item) return null;

      const { data, expiry } = JSON.parse(item);
      if (Date.now() > expiry) {
        localStorage.removeItem(this.prefix + key);
        return null;
      }

      return data;
    } catch (e) {
      console.warn(`Cache read error for ${key}:`, e);
      return null;
    }
  },

  /**
   * Set cache with TTL
   * @param {string} key - Cache key
   * @param {any} data - Data to cache
   * @param {number} ttl - Time to live in milliseconds (default 5 min)
   */
  set(key, data, ttl = this.defaultTTL) {
    try {
      const item = {
        data,
        expiry: Date.now() + ttl
      };
      localStorage.setItem(this.prefix + key, JSON.stringify(item));
    } catch (e) {
      console.warn(`Cache write error for ${key}:`, e);
    }
  },

  /**
   * Clear all cached data
   */
  clear() {
    try {
      Object.keys(localStorage).forEach(key => {
        if (key.startsWith(this.prefix)) {
          localStorage.removeItem(key);
        }
      });
    } catch (e) {
      console.warn('Cache clear error:', e);
    }
  }
};

/**
 * Lazy loading utilities
 */
const LazyLoader = {
  /**
   * Load image with lazy loading
   * @param {string} src - Image URL
   * @param {HTMLElement} img - Image element
   */
  loadImage(src, img) {
    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            img.src = src;
            observer.unobserve(img);
          }
        });
      });
      observer.observe(img);
    } else {
      img.src = src; // Fallback for older browsers
    }
  },

  /**
   * Defer non-critical operations
   * @param {Function} callback - Function to defer
   * @param {number} delay - Delay in milliseconds
   */
  defer(callback, delay = 1000) {
    if ('requestIdleCallback' in window) {
      requestIdleCallback(() => callback(), { timeout: delay });
    } else {
      setTimeout(callback, delay);
    }
  }
};

/**
 * Debounce utility for expensive operations
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function} Debounced function
 */
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

/**
 * Request animation frame throttle
 * @param {Function} func - Function to throttle
 * @returns {Function} Throttled function
 */
function throttleRAF(func) {
  let ticking = false;
  return function(...args) {
    if (!ticking) {
      requestAnimationFrame(() => {
        func(...args);
        ticking = false;
      });
      ticking = true;
    }
  };
}

// Log initial performance metrics on page load
window.addEventListener('load', () => {
  PerformanceMonitor.markPageLoadComplete();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { PerformanceMonitor, CacheManager, LazyLoader, debounce, throttleRAF };
}
