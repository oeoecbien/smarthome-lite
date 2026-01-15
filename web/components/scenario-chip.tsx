import { cn } from "@/lib/utils"
import { Sun, Moon, Sunset, UserX } from "lucide-react"
import type { ScenarioType } from "@/lib/types"

interface ScenarioChipProps {
  scenario: ScenarioType
  confidence?: number
  className?: string
}

const scenarioConfig: Record<ScenarioType, { label: string; icon: typeof Sun; colorClass: string }> = {
  0: {
    label: "Jour",
    icon: Sun,
    colorClass: "bg-day/20 text-day",
  },
  1: {
    label: "Nuit",
    icon: Moon,
    colorClass: "bg-night/20 text-night",
  },
  2: {
    label: "Absence",
    icon: UserX,
    colorClass: "bg-away/20 text-away",
  },
  3: {
    label: "Soirée",
    icon: Sunset,
    colorClass: "bg-evening/20 text-evening",
  },
}

export function ScenarioChip({ scenario, confidence, className }: ScenarioChipProps) {
  const config = scenarioConfig[scenario]
  const Icon = config.icon

  return (
    <div
      className={cn(
        "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium",
        config.colorClass,
        className,
      )}
    >
      <Icon className="h-4 w-4" />
      <span>{config.label}</span>
      {confidence !== undefined && <span className="opacity-70">({Math.round(confidence * 100)}%)</span>}
    </div>
  )
}
