import { cn } from "@/lib/utils"
import { Sun, Moon, Sunset, UserX, Info } from "lucide-react"
import type { ScenarioType } from "@/lib/types"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"

interface ScenarioChipProps {
  scenario: ScenarioType
  confidence?: number
  className?: string
  /** Affichage court (ex. tableau de bord) : "Jour (71%)" au lieu de "Jour · Certitude 71%" */
  compact?: boolean
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

const CERTITUDE_TOOLTIP =
  "Certitude du système : plus le pourcentage est élevé, plus l’IA est sûre du scénario. Il dépend de l’heure, de la présence et de l’état des lampes."

export function ScenarioChip({ scenario, confidence, className, compact = false }: ScenarioChipProps) {
  const config = scenarioConfig[scenario]
  const Icon = config.icon
  const certitudePercent = confidence !== undefined ? Math.round(confidence * 100) : null

  const confidenceNode =
    certitudePercent !== null ? (
      <Tooltip>
        <TooltipTrigger asChild>
          <span
            className={cn(
              "inline-flex items-center gap-1 opacity-80 cursor-help border-b border-dotted border-current/50",
              compact && "border-none",
            )}
          >
            {compact ? (
              `(${certitudePercent}%)`
            ) : (
              <>
                · Certitude {certitudePercent}%
                <Info className="h-3.5 w-3.5 shrink-0 opacity-70" aria-hidden />
              </>
            )}
          </span>
        </TooltipTrigger>
        <TooltipContent side="bottom" className="max-w-[260px]">
          {CERTITUDE_TOOLTIP}
        </TooltipContent>
      </Tooltip>
    ) : null

  return (
    <div
      className={cn(
        "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium flex-wrap",
        config.colorClass,
        className,
      )}
    >
      <Icon className="h-4 w-4 shrink-0" />
      <span>{config.label}</span>
      {confidenceNode}
    </div>
  )
}
