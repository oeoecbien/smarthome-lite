import { api } from "@/lib/api"
import type { LightReading } from "@/lib/types"

export const lightReadingService = {
  async getLightReadings(raspberryPiId?: number, limit?: number): Promise<LightReading[]> {
    const params: Record<string, string | number> = { limit: limit ?? 100 }
    if (raspberryPiId != null && raspberryPiId > 0) {
      params.raspberry_pi_id = raspberryPiId
    }
    return api.get<LightReading[]>("/api/light-readings", params)
  },

  /** Crée une mesure manuellement (admin). */
  async createLightReadingManual(payload: {
    raspberry_pi_id: number
    lux_value: number
    sensor_type?: string
  }): Promise<LightReading> {
    return api.post<LightReading>("/api/light-readings/manual", {
      raspberry_pi_id: payload.raspberry_pi_id,
      lux_value: payload.lux_value,
      sensor_type: payload.sensor_type ?? "BH1750",
    })
  },
}
