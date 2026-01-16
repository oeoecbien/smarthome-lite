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
}
