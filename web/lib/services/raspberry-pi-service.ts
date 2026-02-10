import { api } from "@/lib/api"
import type { ZwaveSensorData, ZwaveKnownDevice } from "@/lib/types"

export interface RaspberryPi {
  id: number
  name: string
  location?: string
  ip_address: string
  api_key: string
  is_online: boolean
  created_at: string
  updated_at?: string
  device_count?: number
}

export interface AvailableRaspberryPi {
  id: number
  name: string
  location?: string
}

export interface RaspberryPiCreate {
  name: string
  location?: string
  ip_address: string
}

export interface RaspberryPiUpdate {
  name?: string
  location?: string
  ip_address?: string
  is_online?: boolean
  api_key?: string
}

export const raspberryPiService = {
  async getAvailableRaspberryPis(): Promise<AvailableRaspberryPi[]> {
    return api.get<AvailableRaspberryPi[]>("/api/raspberry-pis/available")
  },

  async getRaspberryPis(): Promise<RaspberryPi[]> {
    return api.get<RaspberryPi[]>("/api/raspberry-pis")
  },

  async getRaspberryPi(id: number): Promise<RaspberryPi> {
    return api.get<RaspberryPi>(`/api/raspberry-pis/${id}`)
  },

  async createRaspberryPi(data: RaspberryPiCreate): Promise<RaspberryPi> {
    return api.post<RaspberryPi>("/api/raspberry-pis", data)
  },

  async updateRaspberryPi(id: number, data: RaspberryPiUpdate): Promise<RaspberryPi> {
    return api.put<RaspberryPi>(`/api/raspberry-pis/${id}`, data)
  },

  async deleteRaspberryPi(id: number): Promise<void> {
    return api.delete(`/api/raspberry-pis/${id}`)
  },

  /** Données capteur d'un nœud Z-Wave sur ce RPi. Lecture lente (7× getValue 10s) : timeout 95s. */
  async getNodeSensor(rpiId: number, nodeId: number): Promise<ZwaveSensorData> {
    return api.get<ZwaveSensorData>(`/api/raspberry-pis/${rpiId}/nodes/${nodeId}/sensor`, undefined, {
      timeout: 95_000,
    })
  },

  /**
   * Flux temps réel des données capteur (Server-Sent Events).
   * Retourne une fonction pour fermer la connexion.
   */
  subscribeNodeSensorStream(
    rpiId: number,
    nodeId: number,
    onData: (data: ZwaveSensorData & { error?: string }) => void,
    onError?: (err: Error) => void
  ): { abort: () => void } {
    return api.subscribeToStream<ZwaveSensorData & { error?: string }>(
      `/api/raspberry-pis/${rpiId}/nodes/${nodeId}/sensor/stream`,
      onData,
      onError
    )
  },
}

/** Service admin pour les appareils Z-Wave connus (registre backend). */
export const zwaveService = {
  async getKnownDevices(): Promise<ZwaveKnownDevice[]> {
    return api.get<ZwaveKnownDevice[]>("/api/admin/zwave-devices")
  },
}
