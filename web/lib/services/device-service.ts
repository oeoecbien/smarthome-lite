import { api } from "@/lib/api"
import type { Device } from "@/lib/types"

export const deviceService = {
  async getDevices(location?: string, type?: string): Promise<Device[]> {
    return api.get<Device[]>("/api/devices", { location, type })
  },

  async getDevice(id: number): Promise<Device> {
    return api.get<Device>(`/api/devices/${id}`)
  },

  async createDevice(data: Omit<Device, "id" | "state" | "brightness">): Promise<Device> {
    return api.post<Device>("/api/devices", data)
  },

  async updateState(id: number, state: "ON" | "OFF"): Promise<Device> {
    return api.put<Device>(`/api/devices/${id}/state`, { state })
  },

  async updateBrightness(id: number, brightness: number): Promise<Device> {
    return api.put<Device>(`/api/devices/${id}/brightness`, { brightness })
  },

  async deleteDevice(id: number): Promise<void> {
    return api.delete(`/api/devices/${id}`)
  },
}
