import { api } from "@/lib/api"

export interface BluetoothDevice {
  id: number
  user_id: number
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

export const bluetoothDeviceService = {
  async list(): Promise<BluetoothDevice[]> {
    return api.get<BluetoothDevice[]>("/api/admin/bluetooth-devices")
  },

  async create(data: BluetoothDeviceCreate): Promise<BluetoothDevice> {
    return api.post<BluetoothDevice>("/api/admin/bluetooth-devices", data)
  },

  async delete(id: number): Promise<void> {
    return api.delete(`/api/admin/bluetooth-devices/${id}`)
  },
}
