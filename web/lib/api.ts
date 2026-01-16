// API Client with JWT interceptors

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"
const API_TIMEOUT = Number.parseInt(process.env.NEXT_PUBLIC_API_TIMEOUT || "10000", 10)

interface ApiError {
  detail?: string
  message?: string
}

class ApiClient {
  private baseUrl: string
  private timeout: number

  constructor() {
    this.baseUrl = API_BASE_URL
    this.timeout = API_TIMEOUT
  }

  private getToken(): string | null {
    if (typeof window === "undefined") return null
    return localStorage.getItem("auth_token")
  }

  private getHeaders(): HeadersInit {
    const headers: HeadersInit = {
      "Content-Type": "application/json",
    }
    const token = this.getToken()
    if (token) {
      headers["Authorization"] = `Bearer ${token}`
    }
    return headers
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (response.status === 401) {
      // Clear auth and redirect to login
      if (typeof window !== "undefined") {
        localStorage.removeItem("auth_token")
        localStorage.removeItem("auth_user")
        window.location.href = "/login"
      }
      throw new Error("Session expirée. Veuillez vous reconnecter.")
    }

    if (!response.ok) {
      let errorMessage = `Erreur ${response.status}`
      
      // Try to parse JSON error response
      try {
        const contentType = response.headers.get("content-type")
        if (contentType && contentType.includes("application/json")) {
          const error: ApiError = await response.json()
          errorMessage = error.detail || error.message || errorMessage
        } else {
          // If not JSON, try to get text
          const text = await response.text()
          if (text) {
            errorMessage = text.length > 200 ? `${text.substring(0, 200)}...` : text
          }
        }
      } catch (parseError) {
        // If parsing fails, use status text or default message
        errorMessage = response.statusText || errorMessage
      }
      
      throw new Error(errorMessage)
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return undefined as T
    }

    return response.json()
  }

  async get<T>(endpoint: string, params?: Record<string, string | number | boolean | undefined>): Promise<T> {
    const url = new URL(`${this.baseUrl}${endpoint}`)
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== "") {
          url.searchParams.append(key, String(value))
        }
      })
    }

    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), this.timeout)

    try {
      const response = await fetch(url.toString(), {
        method: "GET",
        headers: this.getHeaders(),
        signal: controller.signal,
      })
      return this.handleResponse<T>(response)
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError") {
        throw new Error("La requête a expiré. Vérifiez votre connexion.")
      }
      throw error
    } finally {
      clearTimeout(timeoutId)
    }
  }

  async post<T>(endpoint: string, data?: unknown): Promise<T> {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), this.timeout)

    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: "POST",
        headers: this.getHeaders(),
        body: data ? JSON.stringify(data) : undefined,
        signal: controller.signal,
      })
      return this.handleResponse<T>(response)
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError") {
        throw new Error("La requête a expiré. Vérifiez votre connexion.")
      }
      throw error
    } finally {
      clearTimeout(timeoutId)
    }
  }

  async put<T>(endpoint: string, data?: unknown): Promise<T> {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), this.timeout)

    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: "PUT",
        headers: this.getHeaders(),
        body: data ? JSON.stringify(data) : undefined,
        signal: controller.signal,
      })
      return this.handleResponse<T>(response)
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError") {
        throw new Error("La requête a expiré. Vérifiez votre connexion.")
      }
      throw error
    } finally {
      clearTimeout(timeoutId)
    }
  }

  async delete<T>(endpoint: string): Promise<T> {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), this.timeout)

    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: "DELETE",
        headers: this.getHeaders(),
        signal: controller.signal,
      })
      return this.handleResponse<T>(response)
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError") {
        throw new Error("La requête a expiré. Vérifiez votre connexion.")
      }
      throw error
    } finally {
      clearTimeout(timeoutId)
    }
  }

  // Special method for form-urlencoded (login)
  async postForm<T>(endpoint: string, data: URLSearchParams): Promise<T> {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), this.timeout)

    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: data,
        signal: controller.signal,
      })
      return this.handleResponse<T>(response)
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError") {
        throw new Error("La requête a expiré. Vérifiez votre connexion.")
      }
      throw error
    } finally {
      clearTimeout(timeoutId)
    }
  }
}

export const api = new ApiClient()
