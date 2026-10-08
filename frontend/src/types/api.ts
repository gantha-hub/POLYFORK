/**
 * VrikshaVision API Contract Types
 * Strictly aligned with FastAPI backend schemas.
 */

export interface APIError {
  code: string;
  message: string;
  details?: unknown;
}

export interface ResponseEnvelope<T> {
  success: boolean;
  data: T;
  error: APIError | null;
  data_source: "synthetic" | "real";
}

export interface HealthResponse {
  status: string;
  database: string;
  model_backend: "mock" | "torch";
  environment: string;
  app_name: string;
}

export interface ProjectCreate {
  name: string;
  description?: string;
}

export interface ProjectResponse {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface SurveyResponse {
  id: string;
  project_id: string;
  original_filename: string;
  crs: string | null;
  resolution_m: number | null;
  image_width: number | null;
  image_height: number | null;
  capture_date: string | null;
  forest_type: string;
  created_at: string;
}

export interface JobResponse {
  id: string;
  survey_id: string;
  job_type: string;
  status: "queued" | "processing" | "completed" | "failed";
  progress: number;
  error: string | null;
  created_at: string;
  updated_at: string;
}

export interface ConfidenceInterval {
  low: number;
  high: number;
  confidence_level: number;
}

export interface TreeCountResult {
  raw_count: number;
  calibrated_count: number;
  interval: ConfidenceInterval;
  calibrated: boolean;
}

export interface CarbonEstimateResult {
  mean_carbon_kg: number;
  mean_carbon_tonnes: number;
  interval_kg: ConfidenceInterval;
  interval_tonnes: ConfidenceInterval;
  carbon_fraction: number;
}

export interface GeoJSONFeatureProperties {
  tree_id: string;
  survey_id: string;
  crown_area_sqm: number;
  confidence: number;
  dbh_cm: number;
  biomass_kg: number;
  carbon_kg: number;
  status: "detected" | "verified" | "rejected" | "edited";
  data_source: "synthetic" | "real";
  notes: string | null;
}

export interface GeoJSONFeature {
  type: "Feature";
  geometry: {
    type: "Polygon";
    coordinates: number[][][];
  };
  properties: GeoJSONFeatureProperties;
}

export interface GeoJSONFeatureCollection {
  type: "FeatureCollection";
  features: GeoJSONFeature[];
}

export interface SurveyResultsSummary {
  survey_id: string;
  forest_type: string;
  count: TreeCountResult;
  carbon: CarbonEstimateResult;
  mean_crown_area_sqm: number;
  mean_dbh_cm: number;
  total_trees_detected: number;
  data_source: "synthetic" | "real";
  geojson: GeoJSONFeatureCollection | null;
}

export interface CalibrationFitRequest {
  project_id: string;
  method: "negbin_glm" | "ratio";
  confidence_level?: number;
}

export interface CalibrationStatusResponse {
  project_id: string;
  calibrated: boolean;
  model_id?: string;
  method?: "negbin_glm" | "ratio";
  n_plots?: number;
  residual_quantile_q?: number;
  empirical_coverage?: number;
  params?: {
    coefficients: Record<string, number>;
    feature_names: string[];
    dispersion_alpha?: number;
  };
  created_at?: string;
}

export interface ChangeCategoryMetric {
  count: number;
  total_carbon_kg: number;
  mean_crown_area_sqm: number;
  tree_ids: string[];
}

export interface SurveyComparisonResponse {
  survey_1_id: string;
  survey_2_id: string;
  new_trees: ChangeCategoryMetric;
  lost_trees: ChangeCategoryMetric;
  grown_trees: ChangeCategoryMetric;
  unchanged_trees: ChangeCategoryMetric;
  net_tree_change: number;
  net_carbon_change_kg: number;
  data_source: "synthetic" | "real";
}

export interface TreeQueueItem {
  tree_id: string;
  survey_id: string;
  confidence: number;
  crown_area_sqm: number;
  centroid_x: number;
  centroid_y: number;
  geometry_geojson: string;
  priority_score: number;
  audit_reason: string;
  status: string;
  data_source: "synthetic" | "real";
}

export interface VerificationCreate {
  tree_id: string;
  action: "accept" | "reject" | "edit";
  edited_geometry_geojson?: string;
  user_id?: string;
  notes?: string;
}

export interface VerificationResponse {
  id: string;
  tree_id: string;
  action: "accept" | "reject" | "edit";
  user_id: string;
  notes: string | null;
  timestamp: string;
}
