import { api } from "@/lib/api"

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
}
