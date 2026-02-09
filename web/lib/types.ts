// SmartHome Lite Type Definitions

export type UserRole = "user" | "admin"

export interface User {
  id: number
  username: string
  email?: string
  role?: UserRole
}

/** Règles pilotage par capteur (mouvement + luminosité) */
export interface SensorRules {
  motion?: { on_brightness?: number; off_after_seconds?: number }
  illuminance?: { below_lux?: number; brightness?: number; above_lux?: number }
}

export interface Device {
  id: number
  user_id: number
  name: string
  type: "light" | "dimmer" | "socket" | "sensor"
  raspberry_pi_id: number
  gpio_pin: number
  /** État ON/OFF (backend renvoie booléen) */
  state: boolean | "ON" | "OFF"
  brightness: number | null
  location?: string
  /** Nom du RPi (liste appareils) */
  raspberry_pi_name?: string
  /** RPi en ligne = commandes envoyées au vrai hardware */
  raspberry_pi_online?: boolean
  /** ID du capteur qui pilote cette lampe (lampes uniquement) */
  controlled_by_sensor_id?: number | null
  /** Règles : mouvement (allumer / éteindre après X s) et luminosité (seuils lux) */
  sensor_rules?: SensorRules | null
  /** Nom du capteur (affichage) */
  controlled_by_sensor_name?: string | null
}

export interface Rule {
  id: number
  name: string
  description?: string
  condition: RuleCondition
  action: RuleAction
  enabled: boolean
  priority: number
  created_at: string
}

export interface RuleCondition {
  type: "AND" | "OR" | "time" | "presence" | "light"
  conditions?: RuleCondition[]
  operator?: string
  value?: unknown
}

export interface RuleAction {
  device_id: number
  action: "turn_on" | "turn_off" | "set_brightness"
  brightness?: number
}

export type ScenarioType = 0 | 1 | 2 | 3
export const SCENARIO_LABELS: Record<ScenarioType, string> = {
  0: "Day",
  1: "Night",
  2: "Away",
  3: "Evening",
}

/** Contexte du scénario actuel (mouvement MultiSensor7, lampes). */
export interface CurrentScenarioContext {
  hour: number
  day_of_week: number
  presence_detected: boolean
  light_on: boolean
  raspberry_pi_id?: number
  detected_users: number[]
  detected_usernames: string[]
  user_count: number
}

export interface CurrentScenario {
  scenario: ScenarioType
  scenario_name?: string
  confidence?: number
  method?: string
  /** Contexte utilisé pour la classification (présence, lampes, utilisateurs détectés). */
  context?: CurrentScenarioContext
  features?: Record<string, unknown>
}

export interface ClassifyRequest {
  hour: number
  day_of_week: number
  presence_detected: boolean
  light_on: boolean
}

export interface ClassifyResponse {
  scenario: ScenarioType
  confidence: number
}

export interface PredictIntensityRequest {
  hour: number
  day_of_week: number
  lux_value: number
  presence_detected: boolean
  scenario: ScenarioType
}

export interface PredictIntensityResponse {
  intensity: number
  confidence?: number
  method?: string
}

export interface ModelMetrics {
  model_loaded: boolean
  accuracy?: number
  scenarios?: string[]
  features?: string[]
}

export interface SmartDimmingStatus {
  enabled: boolean
  adjustments_today?: number
  active_devices?: number[]
}

export interface SmartDimmingAdjustment {
  id: number
  device_id: number
  device_name?: string
  brightness_before: number
  brightness_after: number
  scenario: ScenarioType
  reason: string
  timestamp: string
}

export interface PresenceRecord {
  id: number
  raspberry_pi_id: number
  raspberry_pi_name?: string
  location?: string
  detected_at: string
  sensor_node_id?: number
}

export interface LightReading {
  id: number
  raspberry_pi_id: number
  lux: number
  percentage: number
  timestamp: string
}

export interface SystemEvent {
  id: number
  device_id?: number
  device_name?: string
  event_type: string
  value?: string
  source: string
  timestamp: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
}

export interface RuleTestResult {
  matched: boolean
  reason?: string
}

/** Données capteur d'un nœud Z-Wave (ex. Aeotec MultiSensor 7). */
export interface ZwaveSensorData {
  success?: boolean
  node_id: number
  motion: boolean
  temperature_c: number | null
  humidity: number | null
  illuminance_lux: number | null
  ultraviolet: number | null
  battery_percent: number | null
  device_type: string | null
  device_name: string | null
  device_model: string | null
}

/** Appareil Z-Wave connu par le backend (registre). */
export interface ZwaveKnownDevice {
  manufacturer_id: number
  manufacturer_name: string
  product_type: number
  product_id: number
  model: string
  name: string
  full_name: string
  sensor_capabilities: string[]
}
