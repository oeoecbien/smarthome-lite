import { api } from "@/lib/api"
import type { SmartDimmingStatus, SmartDimmingAdjustment } from "@/lib/types"

export const smartDimmingService = {
  async getStatus(): Promise<SmartDimmingStatus> {
    return api.get<SmartDimmingStatus>("/api/smart-dimming/status")
  },

  async enable(enabled: boolean): Promise<SmartDimmingStatus> {
    return api.put<SmartDimmingStatus>("/api/smart-dimming/enable", { enabled })
  },

  async getAdjustments(deviceId?: number, limit?: number): Promise<SmartDimmingAdjustment[]> {
    return api.get<SmartDimmingAdjustment[]>("/api/smart-dimming/adjustments", {
      device_id: deviceId,
      limit,
    })
  },

  async pauseDevice(deviceId: number): Promise<void> {
    return api.put(`/api/smart-dimming/pause/${deviceId}`)
  },

  /**
   * Simule une mesure de luminosité pour déclencher le Smart Dimming (sans capteur).
   * Sans paramètres : utilise le premier RPi avec lampe allumée et 500 lux.
   */
  async simulateReading(raspberryPiId?: number, luxValue?: number): Promise<{
    light_reading_id: number
    lux_value: number
    adjustments_count: number
    adjustments: Array<{
      device_id: number
      device_name: string
      previous_brightness: number
      target_brightness: number
      applied_brightness?: number
      reason: string
      scenario: number
    }>
  }> {
    return api.post("/api/smart-dimming/simulate-reading", {
      raspberry_pi_id: raspberryPiId ?? undefined,
      lux_value: luxValue ?? 500,
    })
  },
}
