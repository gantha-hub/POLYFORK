import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import type { GeoJSONFeatureCollection, GeoJSONFeatureProperties } from '../../types/api';
import { Maximize2, Sparkles, Eye } from 'lucide-react';

interface StandMapProps {
  geojson: GeoJSONFeatureCollection | null;
  selectedTreeId: string | null;
  onSelectTree: (tree: GeoJSONFeatureProperties) => void;
}

export const StandMap: React.FC<StandMapProps> = ({
  geojson,
  selectedTreeId,
  onSelectTree,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const geojsonLayerRef = useRef<L.GeoJSON | null>(null);
  const baseTileLayerRef = useRef<L.TileLayer | null>(null);

  const [mapStyle, setMapStyle] = useState<'dark' | 'satellite'>('dark');
  const [colorMode, setColorMode] = useState<'carbon' | 'status'>('carbon');

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current, {
        center: [12.9716, 77.5946], // Default coordinates
        zoom: 17,
        zoomControl: false,
        attributionControl: false,
        preferCanvas: true, // Hardware accelerated canvas rendering for smooth touch panning
      });

      L.control.zoom({ position: 'bottomright' }).addTo(map);

      // Default dark basemap (Zero-key ESRI World Dark Gray Canvas)
      const darkLayer = L.tileLayer(
        'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
        {
          maxZoom: 19,
          attribution: 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ',
        }
      ).addTo(map);

      baseTileLayerRef.current = darkLayer;
      mapInstanceRef.current = map;
    }

    return () => {
      // Map cleanup on unmount
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Update base tile layer on style change
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    if (baseTileLayerRef.current) {
      map.removeLayer(baseTileLayerRef.current);
    }

    if (mapStyle === 'satellite') {
      const satLayer = L.tileLayer(
        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        { maxZoom: 20 }
      ).addTo(map);
      baseTileLayerRef.current = satLayer;
    } else {
      const darkLayer = L.tileLayer(
        'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
        { maxZoom: 19, attribution: 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ' }
      ).addTo(map);
      baseTileLayerRef.current = darkLayer;
    }
  }, [mapStyle]);

  // Color calculation helper
  const getFeatureStyle = (properties: GeoJSONFeatureProperties) => {
    const isSelected = properties.tree_id === selectedTreeId;

    if (isSelected) {
      return {
        color: '#fbbf24',
        weight: 3.5,
        opacity: 1,
        fillColor: '#f59e0b',
        fillOpacity: 0.65,
      };
    }

    if (colorMode === 'status') {
      let fillColor = '#64748b'; // default detected
      if (properties.status === 'verified') fillColor = '#10b981';
      if (properties.status === 'rejected') fillColor = '#ef4444';
      if (properties.status === 'edited') fillColor = '#38bdf8';

      return {
        color: fillColor,
        weight: 1.5,
        opacity: 0.85,
        fillColor,
        fillOpacity: 0.35,
      };
    }

    // Default: Color by Carbon stock
    const carbon = properties.carbon_kg || 0;
    let fillColor = '#6ee7b7';
    if (carbon > 200) fillColor = '#047857';
    else if (carbon > 120) fillColor = '#059669';
    else if (carbon > 60) fillColor = '#10b981';
    else if (carbon > 25) fillColor = '#34d399';

    return {
      color: '#34d399',
      weight: 1.2,
      opacity: 0.9,
      fillColor,
      fillOpacity: 0.45,
    };
  };

  // Render GeoJSON polygons
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    if (geojsonLayerRef.current) {
      map.removeLayer(geojsonLayerRef.current);
      geojsonLayerRef.current = null;
    }

    if (!geojson || !geojson.features || geojson.features.length === 0) {
      return;
    }

    const layer = L.geoJSON(geojson as any, {
      style: (feature) => {
        if (!feature || !feature.properties) return {};
        return getFeatureStyle(feature.properties as GeoJSONFeatureProperties);
      },
      onEachFeature: (feature, layerItem) => {
        const props = feature.properties as GeoJSONFeatureProperties;
        if (!props) return;

        // Tooltip
        layerItem.bindTooltip(
          `
          <div style="font-family: var(--font-sans); padding: 2px 4px;">
            <strong style="color: #10b981;">Tree #${props.tree_id.slice(-6)}</strong><br/>
            <span>Area: ${props.crown_area_sqm.toFixed(1)} m²</span><br/>
            <span>Carbon: ${props.carbon_kg.toFixed(1)} kg</span><br/>
            <span style="font-size: 10px; color: #94a3b8;">${props.status.toUpperCase()}</span>
          </div>
          `,
          { className: 'tree-leaflet-tooltip', sticky: true }
        );

        // Click listener
        layerItem.on('click', () => {
          onSelectTree(props);
        });
      },
    }).addTo(map);

    geojsonLayerRef.current = layer;

    // Zoom to fit bounds
    try {
      const bounds = layer.getBounds();
      if (bounds.isValid()) {
        map.fitBounds(bounds, { padding: [50, 50], maxZoom: 19 });
      }
    } catch {
      // Ignored if empty bounds
    }
  }, [geojson, colorMode, selectedTreeId]);

  const handleZoomToFit = () => {
    if (geojsonLayerRef.current && mapInstanceRef.current) {
      try {
        const bounds = geojsonLayerRef.current.getBounds();
        if (bounds.isValid()) {
          mapInstanceRef.current.fitBounds(bounds, { padding: [50, 50] });
        }
      } catch {
        // Ignored
      }
    }
  };

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%', overflow: 'hidden' }}>
      {/* Map Canvas */}
      <div
        ref={mapContainerRef}
        style={{ width: '100%', height: '100%', background: '#060a08' }}
      />

      {/* Floating Controls Bar */}
      <div className="map-controls-overlay">
        {/* Basemap Toggle */}
        <div
          className="glass-card"
          style={{
            display: 'flex',
            padding: '0.2rem',
            background: 'rgba(9, 15, 12, 0.92)',
            border: '1px solid var(--border-card)',
            borderRadius: 'var(--radius-md)',
          }}
        >
          <button
            onClick={() => setMapStyle('dark')}
            className={`btn touch-target ${mapStyle === 'dark' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ padding: '0.25rem 0.65rem', fontSize: '0.75rem', height: 34, minHeight: 34 }}
          >
            Dark Vector
          </button>
          <button
            onClick={() => setMapStyle('satellite')}
            className={`btn touch-target ${mapStyle === 'satellite' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ padding: '0.25rem 0.65rem', fontSize: '0.75rem', height: 34, minHeight: 34 }}
          >
            Satellite
          </button>
        </div>

        {/* Color Coding Mode */}
        <div
          className="glass-card"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.35rem',
            padding: '0.2rem 0.5rem',
            background: 'rgba(9, 15, 12, 0.92)',
            border: '1px solid var(--border-card)',
            borderRadius: 'var(--radius-md)',
            height: 38,
          }}
        >
          <Sparkles size={15} color="var(--emerald-400)" />
          <select
            aria-label="Canopy Color Scheme"
            className="input-field"
            value={colorMode}
            onChange={(e) => setColorMode(e.target.value as 'carbon' | 'status')}
            style={{
              padding: '0.2rem 1.6rem 0.2rem 0.5rem',
              fontSize: '0.75rem',
              height: 32,
              background: 'transparent',
              border: 'none',
              width: 140,
            }}
          >
            <option value="carbon">Color: Carbon Stock</option>
            <option value="status">Color: Audit Status</option>
          </select>
        </div>

        {/* Fit Bounds Button */}
        <button
          onClick={handleZoomToFit}
          className="btn btn-secondary touch-target"
          title="Zoom to Fit Stand Extents"
          style={{
            height: 38,
            minHeight: 38,
            padding: '0 0.75rem',
            background: 'rgba(9, 15, 12, 0.92)',
            borderColor: 'var(--border-card)',
            borderRadius: 'var(--radius-md)',
          }}
        >
          <Maximize2 size={15} />
          <span style={{ fontSize: '0.75rem' }}>Fit Stand</span>
        </button>

        {/* Canopy Statistics Badge */}
        {geojson && (
          <div
            className="glass-card font-mono"
            style={{
              padding: '0.35rem 0.65rem',
              fontSize: '0.75rem',
              background: 'rgba(9, 15, 12, 0.92)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              height: 38,
            }}
          >
            <Eye size={14} color="var(--emerald-400)" />
            <span style={{ color: 'var(--text-secondary)' }}>
              <strong style={{ color: '#ffffff' }}>{geojson.features.length}</strong> crowns
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
