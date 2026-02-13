// API Client with JWT interceptors

// Injectées par next.config depuis le .env racine (BACKEND_URL → NEXT_PUBLIC_API_BASE_URL)
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"
const API_TIMEOUT = Number.parseInt(process.env.NEXT_PUBLIC_API_TIMEOUT || "10000", 10)

/** URL de l’API utilisée par le client (pour affichage en cas d’erreur de connexion). */
export function getApiBaseUrl(): string {
  return API_BASE_URL
}

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

  /**
   * Souscription à un flux Server-Sent Events (GET avec Authorization).
   * Retourne un objet avec abort() pour fermer la connexion.
   */
  subscribeToStream<T = unknown>(
    endpoint: string,
    onMessage: (data: T) => void,
    onError?: (err: Error) => void
  ): { abort: () => void } {
    const url = `${this.baseUrl}${endpoint}`
    const controller = new AbortController()
    let buffer = ""
    const processLine = (line: string) => {
      if (line.startsWith("data:")) {
        const raw = line.slice(5).trim()
        if (raw === "[DONE]" || !raw) return
        try {
          const data = JSON.parse(raw) as T
          onMessage(data)
        } catch {
          // ignore invalid json
        }
      }
    }
    const run = async () => {
      try {
        const response = await fetch(url, {
          method: "GET",
          headers: this.getHeaders(),
          signal: controller.signal,
        })
        if (!response.ok) {
          if (response.status === 401 && typeof window !== "undefined") {
            localStorage.removeItem("auth_token")
            localStorage.removeItem("auth_user")
            window.location.href = "/login"
            return
          }
          const errBody = await response.text()
          onError?.(new Error(errBody || `HTTP ${response.status}`))
          return
        }
        const reader = response.body?.getReader()
        if (!reader) {
          onError?.(new Error("Stream non disponible"))
          return
        }
        const decoder = new TextDecoder()
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split("\n")
          buffer = lines.pop() ?? ""
          for (const line of lines) processLine(line)
        }
        if (buffer) processLine(buffer)
      } catch (e) {
        if (e instanceof Error && e.name !== "AbortError") {
          onError?.(e)
        }
      }
    }
    run()
    return {
      abort: () => controller.abort(),
    }
  }

  async get<T>(
    endpoint: string,
    params?: Record<string, string | number | boolean | undefined>,
    options?: { timeout?: number }
  ): Promise<T> {
    const url = new URL(`${this.baseUrl}${endpoint}`)
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== "") {
          url.searchParams.append(key, String(value))
        }
      })
    }

    const timeoutMs = options?.timeout ?? this.timeout
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs)

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
      if (error instanceof TypeError && error.message === "Failed to fetch") {
        throw new Error(
          "Impossible de joindre le backend. Vérifiez que le serveur tourne et que BACKEND_URL dans le .env à la racine du projet pointe vers l'API."
        )
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

  async patch<T>(endpoint: string, data?: unknown): Promise<T> {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), this.timeout)

    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: "PATCH",
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
