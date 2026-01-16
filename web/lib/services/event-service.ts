import { api } from "@/lib/api"
import type { SystemEvent } from "@/lib/types"

export const eventService = {
  async getEvents(deviceId?: number, eventType?: string, source?: string, limit?: number): Promise<SystemEvent[]> {
    return api.get<SystemEvent[]>("/api/events", {
      device_id: deviceId,
      event_type: eventType,
      source,
      limit,
    })
  },

  async getDeviceEvents(deviceId: number, limit?: number): Promise<SystemEvent[]> {
    return api.get<SystemEvent[]>(`/api/events/device/${deviceId}`, { limit })
  },
}
