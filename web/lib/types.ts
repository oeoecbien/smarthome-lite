// SmartHome Lite Type Definitions

export type UserRole = "user" | "admin"

export interface User {
  id: number
  username: string
  email?: string
  role?: UserRole
}

export interface Device {
  id: number
  user_id: number
  name: string
  type: "light" | "dimmer" | "socket"
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

export interface CurrentScenario {
  scenario: ScenarioType
  confidence?: number
  features?: Record<string, unknown>
}

export interface ClassifyRequest {
  hour: number
  day_of_week: number
  presence_detected: boolean
  light_on: boolean
  ambient_light_level: number
  temperature?: number
}

export interface ClassifyResponse {
  scenario: ScenarioType
  confidence: number
}

export interface PredictIntensityRequest {
  ambient_light_lux: number
  hour: number
  day_of_week: number
  user_preference_avg: number
  room_type: string
  scenario: ScenarioType
}

export interface PredictIntensityResponse {
  predicted_brightness: number
  confidence?: number
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
  device_mac_address?: string
  signal_strength?: number
  user_id?: number
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
