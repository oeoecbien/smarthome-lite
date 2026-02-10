import path from "path"
import { readFileSync, existsSync } from "fs"
import { fileURLToPath } from "url"

// Répertoire du fichier de config (web/) → .env racine = ../.env
const __dirname = path.dirname(fileURLToPath(import.meta.url))
const rootEnvPath = path.resolve(__dirname, "..", ".env")

if (existsSync(rootEnvPath)) {
  const content = readFileSync(rootEnvPath, "utf8")
  content.split("\n").forEach((line) => {
    const m = line.match(/^([^#=]+)=(.*)$/)
    if (m) {
      const key = m[1].trim()
      const value = m[2].trim().replace(/^["']|["']$/g, "")
      if (!(key in process.env)) process.env[key] = value
    }
  })
}

/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  // Exposer au client les valeurs du .env racine (BACKEND_URL → URL de l’API)
  env: {
    NEXT_PUBLIC_API_BASE_URL: process.env.BACKEND_URL || "http://localhost:8000",
    NEXT_PUBLIC_API_TIMEOUT: process.env.API_TIMEOUT || "10000",
  },
}

export default nextConfig
