"use client"

import { createContext, useContext, useEffect, useState, useCallback, type ReactNode } from "react"
import type { User } from "@/lib/types"
import { authService } from "@/lib/services/auth-service"

interface AuthContextType {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  isAdmin: boolean
  login: (username: string, password: string) => Promise<{ success: boolean; error?: string }>
  register: (data: { username: string; email?: string; password: string }) => Promise<{
    success: boolean
    error?: string
  }>
  logout: () => void
  checkAuth: () => Promise<boolean>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const checkAuth = useCallback(async (): Promise<boolean> => {
    const storedToken = localStorage.getItem("auth_token")
    if (!storedToken) {
      setIsLoading(false)
      return false
    }

    try {
      const currentUser = await authService.getCurrentUser()
      setUser(currentUser)
      setToken(storedToken)
      localStorage.setItem("auth_user", JSON.stringify(currentUser))
      setIsLoading(false)
      return true
    } catch {
      localStorage.removeItem("auth_token")
      localStorage.removeItem("auth_user")
      setUser(null)
      setToken(null)
      setIsLoading(false)
      return false
    }
  }, [])

  useEffect(() => {
    // Initialize from localStorage
    const storedToken = localStorage.getItem("auth_token")
    const storedUser = localStorage.getItem("auth_user")

    if (storedToken && storedUser) {
      try {
        setToken(storedToken)
        setUser(JSON.parse(storedUser))
      } catch {
        // Invalid stored user
      }
    }

    // Verify token is still valid
    checkAuth()
  }, [checkAuth])

  const login = async (username: string, password: string): Promise<{ success: boolean; error?: string }> => {
    try {
      const response = await authService.login(username, password)
      localStorage.setItem("auth_token", response.access_token)
      setToken(response.access_token)

      // Fetch user info
      const currentUser = await authService.getCurrentUser()
      setUser(currentUser)
      localStorage.setItem("auth_user", JSON.stringify(currentUser))

      return { success: true }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : "Erreur de connexion",
      }
    }
  }

  const register = async (data: { username: string; email?: string; password: string }): Promise<{
    success: boolean
    error?: string
  }> => {
    try {
      await authService.register(data)
      // Auto login after registration
      return login(data.username, data.password)
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : "Erreur d'inscription",
      }
    }
  }

  const logout = () => {
    localStorage.removeItem("auth_token")
    localStorage.removeItem("auth_user")
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token && !!user,
        isLoading,
        isAdmin: user?.role === "admin",
        login,
        register,
        logout,
        checkAuth,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}
