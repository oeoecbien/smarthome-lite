"use client"

import { useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { Slider } from "@/components/ui/slider"
import { deviceService } from "@/lib/services/device-service"
import type { Device } from "@/lib/types"
import { Lightbulb, Plug, SunDim, Loader2, MapPin, Wifi, WifiOff, RefreshCw } from "lucide-react"
import { cn } from "@/lib/utils"
import { toast } from "@/hooks/use-toast"

interface DeviceCardUserProps {
  device: Device
  onUpdate: () => void
}

const deviceIcons = {
  light: Lightbulb,
  dimmer: SunDim,
  socket: Plug,
}

export function DeviceCardUser({ device, onUpdate }: DeviceCardUserProps) {
  const [isUpdating, setIsUpdating] = useState(false)
  const [isSyncing, setIsSyncing] = useState(false)
  const [localBrightness, setLocalBrightness] = useState(device.brightness ?? 100)
  const [isDragging, setIsDragging] = useState(false)

  const Icon = deviceIcons[device.type] || Lightbulb
  const isOn = device.state === true || device.state === "ON"
  const hasBrightness = device.type === "light" || device.type === "dimmer"
  const rpiOnline = device.raspberry_pi_online

  const handleToggle = async (checked: boolean) => {
    if (isUpdating) return
    
    setIsUpdating(true)
    try {
      await deviceService.updateState(device.id, checked)
      onUpdate()
      toast({
        title: "Appareil mis à jour",
        description: `${device.name} a été ${checked ? "allumé" : "éteint"}.`,
      })
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Une erreur est survenue"
      
      let friendlyMessage = errorMessage
      if (errorMessage.includes("not responding")) {
        friendlyMessage = "Le Raspberry Pi ne répond pas. Vérifiez qu'il est en ligne."
      } else if (errorMessage.includes("offline")) {
        friendlyMessage = "Le Raspberry Pi est hors ligne."
      } else if (errorMessage.includes("timeout") || errorMessage.includes("expiré")) {
        friendlyMessage = "La requête a expiré. Vérifiez votre connexion."
      }
      
      toast({
        variant: "destructive",
        title: "Erreur",
        description: `Impossible de modifier l'état de ${device.name}. ${friendlyMessage}`,
      })
      
      onUpdate()
    } finally {
      setIsUpdating(false)
    }
  }

  const handleSyncFromRpi = async () => {
    if (isSyncing) return
    setIsSyncing(true)
    try {
      await deviceService.getDeviceState(device.id, true)
      onUpdate()
      toast({ title: "État synchronisé", description: `État de ${device.name} rafraîchi depuis le Raspberry Pi.` })
    } catch {
      toast({ variant: "destructive", title: "Erreur", description: "Impossible de lire l'état depuis le RPi (hors ligne ou timeout)." })
      onUpdate()
    } finally {
      setIsSyncing(false)
    }
  }

  const handleBrightnessChange = (value: number[]) => {
    setLocalBrightness(value[0])
  }

  const handleBrightnessCommit = async (value: number[]) => {
    setIsDragging(false)
    if (value[0] === device.brightness) return

    setIsUpdating(true)
    try {
      await deviceService.updateBrightness(device.id, value[0])
      onUpdate()
      toast({
        title: "Intensité mise à jour",
        description: `L'intensité de ${device.name} a été réglée à ${value[0]}%.`,
      })
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Une erreur est survenue"
      
      let friendlyMessage = errorMessage
      if (errorMessage.includes("not responding")) {
        friendlyMessage = "Le Raspberry Pi ne répond pas. Vérifiez qu'il est en ligne."
      } else if (errorMessage.includes("offline")) {
        friendlyMessage = "Le Raspberry Pi est hors ligne."
      } else if (errorMessage.includes("timeout") || errorMessage.includes("expiré")) {
        friendlyMessage = "La requête a expiré. Vérifiez votre connexion."
      }
      
      setLocalBrightness(device.brightness ?? 100)
      toast({
        variant: "destructive",
        title: "Erreur",
        description: `Impossible de modifier l'intensité de ${device.name}. ${friendlyMessage}`,
      })
      
      onUpdate()
    } finally {
      setIsUpdating(false)
    }
  }

  return (
    <Card
      className={cn(
        "transition-all duration-200",
        isOn ? "ring-2 ring-secondary/50 shadow-lg" : "shadow-sm",
        isUpdating && "opacity-70",
      )}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-4">
          {/* Icon and Info */}
          <div className="flex items-start gap-3">
            <div
              className={cn(
                "p-3 rounded-xl transition-colors",
                isOn ? "bg-secondary/20 text-secondary" : "bg-muted text-muted-foreground",
              )}
            >
              <Icon className="h-6 w-6" />
            </div>
            <div className="min-w-0">
              <h3 className="font-medium truncate">{device.name}</h3>
              <div className="flex items-center gap-2 mt-0.5">
                <span
                  className={cn(
                    "text-xs px-2 py-0.5 rounded-full",
                    isOn ? "bg-secondary/20 text-secondary" : "bg-muted text-muted-foreground",
                  )}
                >
                  {device.type}
                </span>
                {device.location && (
                  <span className="text-xs text-muted-foreground flex items-center gap-1">
                    <MapPin className="h-3 w-3" />
                    {device.location}
                  </span>
                )}
                {rpiOnline !== undefined && (
                  <span className={cn("text-xs flex items-center gap-1", rpiOnline ? "text-green-600" : "text-muted-foreground")} title={rpiOnline ? "Raspberry Pi en ligne" : "Raspberry Pi hors ligne"}>
                    {rpiOnline ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}
                    {rpiOnline ? "RPi en ligne" : "RPi hors ligne"}
                  </span>
                )}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-muted-foreground hover:text-foreground"
              onClick={handleSyncFromRpi}
              disabled={isSyncing}
              title="Synchroniser l'état depuis le Raspberry Pi"
              aria-label="Synchroniser état RPi"
            >
              {isSyncing ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
            </Button>
            {isUpdating ? (
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            ) : (
              <Switch 
                checked={isOn} 
                onCheckedChange={handleToggle} 
                disabled={isUpdating}
                aria-label={`Toggle ${device.name}`} 
              />
            )}
          </div>
        </div>

        {/* Brightness Slider */}
        {hasBrightness && isOn && (
          <div className="mt-4 pt-4 border-t border-border">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-muted-foreground">Intensité</span>
              <span className="text-sm font-medium">{isDragging ? localBrightness : (device.brightness ?? 100)}%</span>
            </div>
            <Slider
              value={[isDragging ? localBrightness : (device.brightness ?? 100)]}
              min={0}
              max={100}
              step={1}
              onValueChange={handleBrightnessChange}
              onValueCommit={handleBrightnessCommit}
              onPointerDown={() => setIsDragging(true)}
              disabled={isUpdating}
              className="w-full"
            />
          </div>
        )}
      </CardContent>
    </Card>
  )
}
