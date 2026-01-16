"use client"

import { useIsAdmin } from "@/hooks/use-is-admin"
import type { ReactNode } from "react"

interface AdminOnlyProps {
  children: ReactNode
  fallback?: ReactNode
}

export function AdminOnly({ children, fallback = null }: AdminOnlyProps) {
  const isAdmin = useIsAdmin()

  if (!isAdmin) {
    return <>{fallback}</>
  }

  return <>{children}</>
}
