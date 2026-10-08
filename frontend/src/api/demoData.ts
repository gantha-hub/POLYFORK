import type {
  HealthResponse,
  ProjectResponse,
  SurveyResponse,
  SurveyResultsSummary,
  CalibrationStatusResponse,
  SurveyComparisonResponse,
  TreeQueueItem,
  GeoJSONFeature,
} from '../types/api';

export const DEMO_HEALTH: HealthResponse = {
  status: 'healthy',
  database: 'connected (static-demo)',
  model_backend: 'mock',
  environment: 'production-demo',
  app_name: 'VrikshaVision: Tree Digital Twin',
};

export const DEMO_PROJECTS: ProjectResponse[] = [
  {
    id: 'demo-stand-01',
    name: 'Western Ghats Stand - Live Observatory',
    description: 'High-resolution UAV canopy instance segmentation & Split-Conformal carbon quantification',
    created_at: '2026-10-08T19:30:12',
    updated_at: '2026-10-08T19:30:12',
  },
  {
    id: 'demo-stand-02',
    name: 'Nilgiri Biosphere Canopy Audit 2026',
    description: 'Multi-temporal carbon credit certification baseline',
    created_at: '2026-10-08T15:04:46',
    updated_at: '2026-10-08T15:04:46',
  },
];

export const DEMO_SURVEYS: SurveyResponse[] = [
  {
    id: 'survey-demo-2026',
    project_id: 'demo-stand-01',
    original_filename: 'Western_Ghats_Canopy_2026.tif',
    crs: 'EPSG:4326',
    resolution_m: 0.05,
    image_width: 2048,
    image_height: 2048,
    capture_date: '2026-03-15',
    forest_type: 'tropical_broadleaf',
    created_at: '2026-03-15T10:00:00',
  },
  {
    id: 'survey-demo-2024',
    project_id: 'demo-stand-01',
    original_filename: 'Western_Ghats_Baseline_2024.tif',
    crs: 'EPSG:4326',
    resolution_m: 0.05,
    image_width: 2048,
    image_height: 2048,
    capture_date: '2024-03-10',
    forest_type: 'tropical_broadleaf',
    created_at: '2024-03-10T10:00:00',
  },
];

// Generate realistic tree crown polygons in Western Ghats coordinates
function generateDemoFeatures(): GeoJSONFeature[] {
  const centerLat = 12.9716;
  const centerLon = 77.5946;
  const features: GeoJSONFeature[] = [];

  const offsets = [
    [-0.0008, -0.0007, 34.2, 24.1, 142.5, 67.0],
    [-0.0006, -0.0002, 58.5, 32.4, 285.0, 134.0],
    [-0.0005, 0.0004, 28.1, 21.0, 110.2, 51.8],
    [-0.0003, -0.0008, 64.0, 35.8, 340.5, 160.0],
    [-0.0002, -0.0003, 45.0, 28.0, 210.0, 98.7],
    [-0.0001, 0.0002, 52.8, 30.5, 255.4, 120.0],
    [0.0000, 0.0007, 72.4, 38.2, 410.0, 192.7],
    [0.0002, -0.0006, 38.0, 25.4, 165.0, 77.5],
    [0.0003, -0.0001, 61.2, 33.9, 315.0, 148.0],
    [0.0004, 0.0005, 48.5, 29.2, 230.0, 108.1],
    [0.0005, -0.0004, 55.0, 31.8, 275.0, 129.2],
    [0.0006, 0.0001, 68.0, 36.5, 370.0, 173.9],
    [0.0007, -0.0007, 31.5, 22.8, 125.0, 58.7],
    [0.0008, 0.0004, 82.0, 42.0, 510.0, 239.7],
    [0.0001, 0.0009, 41.0, 26.8, 185.0, 86.9],
    [-0.0004, 0.0008, 63.5, 34.8, 335.0, 157.4],
    [-0.0007, 0.0003, 49.0, 29.5, 240.0, 112.8],
    [0.0005, 0.0008, 77.0, 40.1, 460.0, 216.2],
    [-0.0002, 0.0006, 56.4, 32.2, 280.0, 131.6],
    [0.0007, -0.0002, 66.8, 36.0, 360.0, 169.2],
  ];

  offsets.forEach(([dLat, dLon, area, dbh, biomass, carbon], idx) => {
    const lat = centerLat + dLat;
    const lon = centerLon + dLon;
    const r = Math.sqrt(area / Math.PI) * 0.000009; // approximate degrees radius

    // 8-point polygon representing tree canopy crown
    const coords: number[][] = [];
    for (let i = 0; i < 8; i++) {
      const angle = (i * Math.PI) / 4;
      const wobble = 0.85 + Math.sin(idx + i) * 0.15;
      coords.push([lon + Math.cos(angle) * r * wobble, lat + Math.sin(angle) * r * wobble]);
    }
    coords.push(coords[0]); // close polygon

    features.push({
      type: 'Feature',
      geometry: {
        type: 'Polygon',
        coordinates: [coords],
      },
      properties: {
        tree_id: `TREE-WG-${String(idx + 1).padStart(4, '0')}`,
        survey_id: 'survey-demo-2026',
        crown_area_sqm: area,
        confidence: 0.88 + (idx % 10) * 0.011,
        dbh_cm: dbh,
        biomass_kg: biomass,
        carbon_kg: carbon,
        status: idx === 0 ? 'verified' : idx === 3 ? 'rejected' : 'detected',
        data_source: 'synthetic',
        notes: idx === 0 ? 'Verified in field plot audit' : null,
      },
    });
  });

  return features;
}

export const DEMO_RESULTS: SurveyResultsSummary = {
  survey_id: 'survey-demo-2026',
  forest_type: 'tropical_broadleaf',
  count: {
    raw_count: 52,
    calibrated_count: 48.2,
    interval: { low: 46.1, high: 50.3, confidence_level: 0.9 },
    calibrated: true,
  },
  carbon: {
    mean_carbon_kg: 18450.0,
    mean_carbon_tonnes: 18.45,
    interval_kg: { low: 17200.0, high: 19800.0, confidence_level: 0.9 },
    interval_tonnes: { low: 17.2, high: 19.8, confidence_level: 0.9 },
    carbon_fraction: 0.47,
  },
  mean_crown_area_sqm: 52.8,
  mean_dbh_cm: 31.4,
  total_trees_detected: 48,
  data_source: 'synthetic',
  geojson: {
    type: 'FeatureCollection',
    features: generateDemoFeatures(),
  },
};

export const DEMO_CALIBRATION: CalibrationStatusResponse = {
  project_id: 'demo-stand-01',
  calibrated: true,
  model_id: 'cal-negbin-v1',
  method: 'negbin_glm',
  n_plots: 14,
  residual_quantile_q: 1.082,
  empirical_coverage: 0.90,
  params: {
    coefficients: {
      const: -0.061,
      canopy_cover: 0.470,
      log_crown_area: -0.068,
    },
    feature_names: ['const', 'canopy_cover', 'log_crown_area'],
    dispersion_alpha: 0.084,
  },
  created_at: '2026-10-08T19:30:12',
};

export const DEMO_COMPARISON: SurveyComparisonResponse = {
  survey_1_id: 'survey-demo-2024',
  survey_2_id: 'survey-demo-2026',
  new_trees: { count: 12, total_carbon_kg: 3250.0, mean_crown_area_sqm: 24.5, tree_ids: ['TREE-WG-0001', 'TREE-WG-0002'] },
  lost_trees: { count: 3, total_carbon_kg: 1420.0, mean_crown_area_sqm: 38.2, tree_ids: ['TREE-WG-0003'] },
  grown_trees: { count: 28, total_carbon_kg: 8410.0, mean_crown_area_sqm: 46.8, tree_ids: [] },
  unchanged_trees: { count: 8, total_carbon_kg: 2100.0, mean_crown_area_sqm: 34.0, tree_ids: [] },
  net_tree_change: 9,
  net_carbon_change_kg: 1830.0,
  data_source: 'synthetic',
};

export const DEMO_VERIFY_QUEUE: TreeQueueItem[] = [
  {
    tree_id: 'TREE-WG-0004',
    survey_id: 'survey-demo-2026',
    confidence: 0.62,
    crown_area_sqm: 64.0,
    centroid_x: 77.5938,
    centroid_y: 12.9713,
    geometry_geojson: '{}',
    priority_score: 0.88,
    audit_reason: 'high_conformal_uncertainty',
    status: 'pending',
    data_source: 'synthetic',
  },
  {
    tree_id: 'TREE-WG-0007',
    survey_id: 'survey-demo-2026',
    confidence: 0.69,
    crown_area_sqm: 72.4,
    centroid_x: 77.5953,
    centroid_y: 12.9716,
    geometry_geojson: '{}',
    priority_score: 0.76,
    audit_reason: 'edge_boundary_anomaly',
    status: 'pending',
    data_source: 'synthetic',
  },
  {
    tree_id: 'TREE-WG-0014',
    survey_id: 'survey-demo-2026',
    confidence: 0.71,
    crown_area_sqm: 82.0,
    centroid_x: 77.5950,
    centroid_y: 12.9724,
    geometry_geojson: '{}',
    priority_score: 0.68,
    audit_reason: 'unusual_area_dbh_ratio',
    status: 'pending',
    data_source: 'synthetic',
  },
  {
    tree_id: 'TREE-WG-0001',
    survey_id: 'survey-demo-2026',
    confidence: 0.94,
    crown_area_sqm: 34.2,
    centroid_x: 77.5939,
    centroid_y: 12.9708,
    geometry_geojson: '{}',
    priority_score: 0.22,
    audit_reason: 'regular_inspection',
    status: 'verified',
    data_source: 'synthetic',
  },
];
