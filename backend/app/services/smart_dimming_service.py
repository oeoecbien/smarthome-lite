"""
Service Smart Dimming - Adaptation dynamique de l'intensité lumineuse
"""

import logging
from typing import Dict, Optional, List
from sqlalchemy.orm import Session
from datetime import datetime

from app.config import settings
from app.models import Device, LightReading, SmartDimmingAdjustment, Event
from app.services.device_service import DeviceService

logger = logging.getLogger(__name__)

# Import optionnel de AIService
try:
    from app.services.ai_service import AIService
    AI_SERVICE_AVAILABLE = True
except ImportError:
    AI_SERVICE_AVAILABLE = False
    logger.warning("AIService non disponible, utilisation d'un scénario par défaut")

class SmartDimmingService:
    """
    Service pour ajustement automatique de l'intensité lumineuse
    basé sur la luminosité ambiante et le scénario IA
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.ai_service = AIService() if AI_SERVICE_AVAILABLE else None
        self.device_service = DeviceService(db)
    
    def calculate_target_brightness(
        self,
        lux_value: float,
        scenario: int
    ) -> Dict:
        """
        Calcule l'intensité cible selon la luminosité et le scénario
        
        Args:
            lux_value: Valeur de luminosité en lux
            scenario: Scénario actif (0-3)
        
        Returns:
            Dict avec target_brightness et reason
        """
        params = settings.dimming_params.get(scenario, {})
        
        # Scénario non compatible avec smart dimming
        if not params.get("enabled", True):
            return {
                "target_brightness": params.get("fixed_brightness", 30),
                "reason": f"Smart dimming disabled for scenario {scenario}",
                "enabled": False
            }
        
        high_threshold = params.get("high_lux_threshold", 500)
        low_threshold = params.get("low_lux_threshold", 200)
        high_brightness = params.get("high_brightness", 20)
        low_brightness = params.get("low_brightness", 70)
        transition = params.get("transition", "immediate")
        
        # Calculer l'intensité cible par interpolation linéaire
        if lux_value >= high_threshold:
            target = high_brightness
            reason = f"High natural light ({lux_value:.0f} lux)"
        elif lux_value <= low_threshold:
            target = low_brightness
            reason = f"Low natural light ({lux_value:.0f} lux)"
        else:
            # Interpolation linéaire
            ratio = (lux_value - low_threshold) / (high_threshold - low_threshold)
            target = int(low_brightness - ratio * (low_brightness - high_brightness))
            reason = f"Medium natural light ({lux_value:.0f} lux) - interpolated"
        
        return {
            "target_brightness": max(0, min(100, target)),
            "reason": reason,
            "transition": transition,
            "enabled": True
        }
    
    async def process_light_reading(
        self,
        light_reading: LightReading
    ) -> List[Dict]:
        """
        Traite une nouvelle mesure de luminosité et ajuste les appareils
        
        Args:
            light_reading: Mesure de luminosité
        
        Returns:
            Liste des ajustements effectués
        """
        if not settings.smart_dimming_enabled:
            logger.info("Smart dimming globally disabled")
            return []
        
        # Récupérer le scénario actuel
        if self.ai_service:
            scenario_data = self.ai_service.get_current_scenario(
                self.db,
                raspberry_pi_id=light_reading.raspberry_pi_id
            )
            scenario = scenario_data["scenario"]
        else:
            # Scénario par défaut si AIService non disponible
            # 0=Day, 1=Night, 2=Away, 3=Evening
            from datetime import datetime
            hour = datetime.now().hour
            if 6 <= hour < 18:
                scenario = 0  # Day
            elif 18 <= hour < 22:
                scenario = 3  # Evening
            else:
                scenario = 1  # Night
            logger.debug(f"Scénario par défaut: {scenario} (heure: {hour})")
        
        # Récupérer les appareils dimmables allumés du même RPi
        devices = self.db.query(Device).filter(
            Device.raspberry_pi_id == light_reading.raspberry_pi_id,
            Device.type == "dimmer",
            Device.state == True
        ).all()
        
        if not devices:
            logger.info("No dimmable devices active")
            return []
        
        adjustments = []
        
        for device in devices:
            # Calculer intensité cible
            calc_result = self.calculate_target_brightness(
                light_reading.lux_value,
                scenario
            )
            
            if not calc_result.get("enabled", True):
                continue
            
            target_brightness = calc_result["target_brightness"]
            reason = calc_result["reason"]
            transition = calc_result.get("transition", "immediate")
            
            # Vérifier si ajustement nécessaire (seuil de 10%)
            brightness_diff = abs(device.brightness - target_brightness)
            
            if brightness_diff < settings.smart_dimming_threshold:
                logger.debug(
                    f"Device {device.id} - Difference too small ({brightness_diff}%), skipping"
                )
                continue
            
            previous_brightness = device.brightness
            
            # Appliquer l'ajustement via le service device
            try:
                await self.device_service.set_device_brightness(
                    device.id,
                    target_brightness,
                    source="smart_dimming",
                    transition=transition
                )
                
                # Enregistrer l'ajustement
                adjustment = SmartDimmingAdjustment(
                    device_id=device.id,
                    light_reading_id=light_reading.id,
                    scenario=scenario,
                    previous_brightness=previous_brightness,
                    target_brightness=target_brightness,
                    applied_brightness=target_brightness,
                    reason=reason
                )
                
                self.db.add(adjustment)
                self.db.commit()
                
                adjustments.append({
                    "device_id": device.id,
                    "device_name": device.name,
                    "previous_brightness": previous_brightness,
                    "target_brightness": target_brightness,
                    "reason": reason,
                    "scenario": scenario
                })
                
                logger.info(
                    f"[OK] Smart dimming: {device.name} adjusted "
                    f"{previous_brightness}% → {target_brightness}% ({reason})"
                )
                
            except Exception as e:
                logger.error(f"Failed to adjust device {device.id}: {e}")
        
        return adjustments
    
    def get_adjustment_history(
        self,
        device_id: Optional[int] = None,
        limit: int = 50
    ) -> List[SmartDimmingAdjustment]:
        """
        Récupère l'historique des ajustements
        """
        query = self.db.query(SmartDimmingAdjustment).order_by(
            SmartDimmingAdjustment.adjusted_at.desc()
        )
        
        if device_id:
            query = query.filter(SmartDimmingAdjustment.device_id == device_id)
        
        return query.limit(limit).all()
    
    def get_statistics(self) -> Dict:
        """
        Calcule des statistiques sur le smart dimming
        """
        from sqlalchemy import func
        
        total_adjustments = self.db.query(SmartDimmingAdjustment).count()
        
        avg_change = self.db.query(
            func.avg(
                func.abs(
                    SmartDimmingAdjustment.target_brightness - SmartDimmingAdjustment.previous_brightness
                )
            )
        ).scalar() or 0
        
        adjustments_by_scenario = self.db.query(
            SmartDimmingAdjustment.scenario,
            func.count(SmartDimmingAdjustment.id)
        ).group_by(SmartDimmingAdjustment.scenario).all()
        
        return {
            "total_adjustments": total_adjustments,
            "avg_brightness_change": round(float(avg_change), 2),
            "adjustments_by_scenario": {
                scenario: count for scenario, count in adjustments_by_scenario
            },
            "enabled": settings.smart_dimming_enabled
        }