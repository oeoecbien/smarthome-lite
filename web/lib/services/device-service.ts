import { api } from "@/lib/api"
import type { Device } from "@/lib/types"

/** Réponse état d’un appareil (backend ou après sync RPi) */
export interface DeviceStateResponse {
  id: number
  name: string
  state: boolean
  brightness: number
}

export const deviceService = {
  async getDevices(location?: string, type?: string): Promise<Device[]> {
    return api.get<Device[]>("/api/devices", { location, type })
  },

  async getDevice(id: number): Promise<Device> {
    return api.get<Device>(`/api/devices/${id}`)
  },

  /**
   * État actuel (state, brightness).
   * @param sync - si true, le backend interroge le RPi pour l’état réel de la lampe
   */
  async getDeviceState(id: number, sync = false): Promise<DeviceStateResponse> {
    return api.get<DeviceStateResponse>(`/api/devices/${id}/state`, { sync: sync ? "true" : undefined })
  },

  /** Le backend assigne user_id depuis le JWT, inutile de l’envoyer */
  async createDevice(data: Omit<Device, "id" | "state" | "brightness" | "user_id">): Promise<Device> {
    return api.post<Device>("/api/devices", data)
  },

  /** Mise à jour partielle (nom, type, gpio, pilotage par capteur) */
  async updateDevice(
    id: number,
    data: Partial<Pick<Device, "name" | "type" | "gpio_pin" | "controlled_by_sensor_id" | "sensor_rules">>
  ): Promise<Device> {
    return api.patch<Device>(`/api/devices/${id}`, data)
  },

  async updateState(id: number, state: boolean): Promise<DeviceStateResponse> {
    return api.put<DeviceStateResponse>(`/api/devices/${id}/state`, { state })
  },

  async updateBrightness(id: number, brightness: number, transition?: "immediate" | "fade"): Promise<DeviceStateResponse> {
    return api.put<DeviceStateResponse>(`/api/devices/${id}/brightness`, { brightness, transition })
  },

  async deleteDevice(id: number): Promise<void> {
    return api.delete(`/api/devices/${id}`)
  },
}
