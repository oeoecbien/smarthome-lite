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

export interface RaspberryPiCreate {
  name: string
  location?: string
  ip_address: string
}

export interface RaspberryPiUpdate {
  name?: string
  location?: string
  ip_address?: string
}

export const raspberryPiService = {
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
