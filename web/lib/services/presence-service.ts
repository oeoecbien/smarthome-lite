import { api } from "@/lib/api"
import type { PresenceRecord } from "@/lib/types"

export interface RecentDetection {
  device_mac_address: string
  device_name: string | null
  signal_strength: number | null
  detected_at: string
  raspberry_pi_name: string
  location: string
}

export const presenceService = {
  async getPresenceHistory(raspberryPiId?: number, limit?: number): Promise<PresenceRecord[]> {
    return api.get<PresenceRecord[]>("/api/presence", {
      raspberry_pi_id: raspberryPiId,
      limit,
    })
  },

  /** Appareils détectés récemment par le RPi (pour « Lier à mon compte » sans saisir la MAC). */
  async getRecentDetections(minutes: number = 2): Promise<RecentDetection[]> {
    return api.get<RecentDetection[]>("/api/presence/recent", { minutes })
  },
}
