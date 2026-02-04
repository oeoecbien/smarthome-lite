import { api } from "@/lib/api"

export interface BluetoothDevice {
  id: number
  user_id: number | null
  username: string
  mac_address: string
  device_name: string | null
  device_type: string | null
  is_active: boolean
}

export interface BluetoothDeviceCreate {
  user_id: number
  mac_address: string
  device_name?: string | null
  device_type?: string | null
}

/** Pour les apps connectées : l'utilisateur enregistre son propre appareil (sans user_id). */
export interface MyBluetoothDeviceCreate {
  mac_address: string
  device_name?: string | null
  device_type?: string | null
}

export const bluetoothDeviceService = {
  /** Admin : liste tous les appareils. */
  async list(): Promise<BluetoothDevice[]> {
    return api.get<BluetoothDevice[]>("/api/admin/bluetooth-devices")
  },

  /** Admin : associer une MAC à un utilisateur. */
  async create(data: BluetoothDeviceCreate): Promise<BluetoothDevice> {
    return api.post<BluetoothDevice>("/api/admin/bluetooth-devices", data)
  },

  /** Admin : supprimer un appareil. */
  async delete(id: number): Promise<void> {
    return api.delete(`/api/admin/bluetooth-devices/${id}`)
  },

  /** Utilisateur connecté : liste mes appareils Bluetooth. */
  async listMy(): Promise<BluetoothDevice[]> {
    return api.get<BluetoothDevice[]>("/api/bluetooth-devices/me")
  },

  /** Utilisateur connecté : enregistrer mon appareil (MAC → mon compte). */
  async createMy(data: MyBluetoothDeviceCreate): Promise<BluetoothDevice> {
    return api.post<BluetoothDevice>("/api/bluetooth-devices/me", data)
  },

  /** Utilisateur connecté : supprimer un de mes appareils. */
  async deleteMy(id: number): Promise<void> {
    return api.delete(`/api/bluetooth-devices/me/${id}`)
  },
}
