import { api } from "@/lib/api"
import type { LightReading } from "@/lib/types"

export const lightReadingService = {
  async getLightReadings(raspberryPiId?: number, limit?: number): Promise<LightReading[]> {
    return api.get<LightReading[]>("/api/light-readings", {
      raspberry_pi_id: raspberryPiId,
      limit,
    })
  },
}
