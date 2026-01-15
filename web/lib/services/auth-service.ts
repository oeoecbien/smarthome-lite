import { api } from "@/lib/api"
import type { AuthResponse, User } from "@/lib/types"

export const authService = {
  async login(username: string, password: string): Promise<AuthResponse> {
    return api.post<AuthResponse>("/api/auth/login", {
      username,
      password,
    })
  },

  async register(userData: { username: string; email?: string; password: string }): Promise<User> {
    return api.post<User>("/api/auth/register", userData)
  },

  async getCurrentUser(): Promise<User> {
    return api.get<User>("/api/auth/me")
  },
}
