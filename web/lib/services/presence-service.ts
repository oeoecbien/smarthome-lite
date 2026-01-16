import { api } from "@/lib/api"
import type { PresenceRecord } from "@/lib/types"

export const presenceService = {
  async getPresenceHistory(raspberryPiId?: number, limit?: number): Promise<PresenceRecord[]> {
    return api.get<PresenceRecord[]>("/api/presence", {
      raspberry_pi_id: raspberryPiId,
      limit,
    })
  },
}
