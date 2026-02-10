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
}
