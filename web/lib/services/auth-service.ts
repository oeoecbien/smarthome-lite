import { api } from "@/lib/api"
import type { AuthResponse, User } from "@/lib/types"

interface MessageResponse {
  message: string
}

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

  async forgotPassword(usernameOrEmail: string): Promise<MessageResponse> {
    return api.post<MessageResponse>("/api/auth/forgot-password", {
      username_or_email: usernameOrEmail,
    })
  },

  async resetPassword(token: string, newPassword: string): Promise<MessageResponse> {
    return api.post<MessageResponse>("/api/auth/reset-password", {
      token,
      new_password: newPassword,
    })
  },
}
