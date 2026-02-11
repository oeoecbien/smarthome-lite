"""
Moteur de règles d'automatisation IF-THEN.

Ce service évalue les règles d'automatisation stockées en base de données
et exécute les actions correspondantes lorsque les conditions sont satisfaites.
"""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, time, timedelta
from sqlalchemy.orm import Session

from app.models import Rule, Device, Event, Presence, LightReading
from app.services.device_service import DeviceService
from app.utils.validators import validate_rule_condition, validate_rule_action

logger = logging.getLogger(__name__)


class RuleEngine:
    """
    Moteur d'évaluation et d'exécution des règles d'automatisation.
    """
    
    def __init__(self, db: Session):
        """
        Initialise le moteur de règles.
        
        Args:
            db: Session de base de données
        """
        self.db = db
        self.device_service = DeviceService(db)
    
    async def evaluate_rules(
        self,
        trigger_event: Optional[str] = None,
        trigger_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Évalue toutes les règles actives et exécute les actions correspondantes.
        
        Args:
            trigger_event: Type d'événement déclencheur (ex: "presence_detected")
            trigger_data: Données associées à l'événement déclencheur
        
        Returns:
            Liste des règles exécutées avec leurs résultats
        """
        # Récupérer toutes les règles actives, triées par priorité (décroissante)
        rules = self.db.query(Rule).filter(
            Rule.enabled == True
        ).order_by(Rule.priority.desc()).all()
        
        executed_rules = []
        
        for rule in rules:
            try:
                # Évaluer la condition
                condition_met = self._evaluate_condition(
                    rule.condition,
                    trigger_event=trigger_event,
                    trigger_data=trigger_data
                )
                
                if condition_met:
                    # Exécuter l'action
                    result = await self._execute_action(rule.action, rule.id)
                    
                    executed_rules.append({
                        "rule_id": rule.id,
                        "rule_name": rule.name,
                        "action_executed": True,
                        "result": result
                    })
                    
                    # Enregistrer l'événement
                    event = Event(
                        device_id=rule.action.get("device_id"),
                        event_type="rule_triggered",
                        value=f"Rule: {rule.name}",
                        source="automatic"
                    )
                    self.db.add(event)
                    self.db.commit()
                    
                    logger.info(f"[OK] Règle '{rule.name}' (ID: {rule.id}) exécutée")
            except Exception as e:
                logger.error(f"Erreur lors de l'évaluation de la règle {rule.id}: {e}")
                executed_rules.append({
                    "rule_id": rule.id,
                    "rule_name": rule.name,
                    "action_executed": False,
                    "error": str(e)
                })
        
        return executed_rules
    
    def _evaluate_condition(
        self,
        condition: Dict[str, Any],
        trigger_event: Optional[str] = None,
        trigger_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Évalue une condition de règle.
        
        Args:
            condition: Condition à évaluer (format JSONB)
            trigger_event: Événement déclencheur
            trigger_data: Données de l'événement
        
        Returns:
            True si la condition est satisfaite, False sinon
        """
        condition_type = condition.get("type")
        
        if condition_type == "AND":
            # Toutes les sous-conditions doivent être vraies
            sub_conditions = condition.get("conditions", [])
            return all(
                self._evaluate_condition(sub_cond, trigger_event, trigger_data)
                for sub_cond in sub_conditions
            )
        
        elif condition_type == "OR":
            # Au moins une sous-condition doit être vraie
            sub_conditions = condition.get("conditions", [])
            return any(
                self._evaluate_condition(sub_cond, trigger_event, trigger_data)
                for sub_cond in sub_conditions
            )
        
        elif condition_type == "time":
            return self._evaluate_time_condition(condition)
        
        elif condition_type == "presence":
            return self._evaluate_presence_condition(condition, trigger_event, trigger_data)
        
        elif condition_type == "light":
            return self._evaluate_light_condition(condition, trigger_data)
        
        elif condition_type == "scenario":
            return self._evaluate_scenario_condition(condition)
        
        else:
            logger.warning(f"Type de condition inconnu: {condition_type}")
            return False
    
    def _evaluate_time_condition(self, condition: Dict[str, Any]) -> bool:
        """Évalue une condition temporelle."""
        operator = condition.get("operator")
        value = condition.get("value")
        now = datetime.now()
        current_time = now.time()
        
        if operator == "between":
            # Format: ["HH:MM", "HH:MM"]
            start_str, end_str = value
            start_time = self._parse_time(start_str)
            end_time = self._parse_time(end_str)
            
            if start_time <= end_time:
                # Plage normale (ex: 08:00 - 18:00)
                return start_time <= current_time <= end_time
            else:
                # Plage qui traverse minuit (ex: 22:00 - 06:00)
                return current_time >= start_time or current_time <= end_time
        
        elif operator in ["<", ">", "="]:
            target_time = self._parse_time(value)
            
            if operator == "<":
                return current_time < target_time
            elif operator == ">":
                return current_time > target_time
            elif operator == "=":
                return current_time.hour == target_time.hour and current_time.minute == target_time.minute
        
        return False
    
    def _evaluate_presence_condition(
        self,
        condition: Dict[str, Any],
        trigger_event: Optional[str],
        trigger_data: Optional[Dict[str, Any]]
    ) -> bool:
        """Évalue une condition de présence (mouvement MultiSensor7)."""
        expected_presence = condition.get("value", False)

        # Si l'événement déclencheur est une détection de mouvement
        if trigger_event == "presence_detected":
            return expected_presence is True

        # Sinon, vérifier dans la base (5 dernières minutes)
        five_minutes_ago = datetime.now() - timedelta(minutes=5)
        query = self.db.query(Presence).filter(Presence.detected_at >= five_minutes_ago)
        if trigger_data and trigger_data.get("raspberry_pi_id") is not None:
            query = query.filter(Presence.raspberry_pi_id == trigger_data["raspberry_pi_id"])
        presence = query.first()
        actual_presence = presence is not None
        return actual_presence == expected_presence
    
    def _evaluate_light_condition(
        self,
        condition: Dict[str, Any],
        trigger_data: Optional[Dict[str, Any]]
    ) -> bool:
        """Évalue une condition de luminosité."""
        operator = condition.get("operator")
        threshold = condition.get("value")
        
        # Récupérer la dernière mesure de luminosité
        query = self.db.query(LightReading).order_by(
            LightReading.measured_at.desc()
        )
        
        if trigger_data and "raspberry_pi_id" in trigger_data:
            query = query.filter(
                LightReading.raspberry_pi_id == trigger_data["raspberry_pi_id"]
            )
        
        latest_reading = query.first()
        
        if not latest_reading:
            return False
        
        current_lux = latest_reading.lux_value
        
        if operator == "<":
            return current_lux < threshold
        elif operator == ">":
            return current_lux > threshold
        elif operator == "=":
            return abs(current_lux - threshold) < 10  # Tolérance de 10 lux
        
        return False
    
    def _evaluate_scenario_condition(self, condition: Dict[str, Any]) -> bool:
        """Évalue une condition de scénario IA."""
        expected_scenario = condition.get("value")
        
        # Utiliser le service IA pour obtenir le scénario actuel
        try:
            from app.services.ai_service import get_ai_service
            ai_service = get_ai_service()
            scenario_data = ai_service.get_current_scenario(self.db)
            current_scenario = scenario_data["scenario"]
            
            return current_scenario == expected_scenario
        except Exception as e:
            logger.error(f"Erreur lors de l'évaluation du scénario: {e}")
            return False
    
    async def _execute_action(
        self,
        action: Dict[str, Any],
        rule_id: int
    ) -> Dict[str, Any]:
        """
        Exécute une action de règle.
        
        Args:
            action: Action à exécuter (format JSONB)
            rule_id: ID de la règle (pour logging)
        
        Returns:
            Résultat de l'exécution
        """
        action_type = action.get("action")
        device_id = action.get("device_id")
        
        if not device_id:
            raise ValueError("device_id manquant dans l'action")
        
        device = self.db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise ValueError(f"Appareil {device_id} introuvable")
        
        if action_type == "turn_on":
            await self.device_service.set_device_state(
                device_id,
                True,
                source="automatic"
            )
            return {"action": "turn_on", "device_id": device_id, "status": "success"}
        
        elif action_type == "turn_off":
            await self.device_service.set_device_state(
                device_id,
                False,
                source="automatic"
            )
            return {"action": "turn_off", "device_id": device_id, "status": "success"}
        
        elif action_type == "set_brightness":
            brightness = action.get("brightness", 50)
            if brightness < 0 or brightness > 100:
                raise ValueError(f"Intensité invalide: {brightness} (doit être 0-100)")
            
            await self.device_service.set_device_brightness(
                device_id,
                brightness,
                source="automatic",
                transition="fade"
            )
            return {
                "action": "set_brightness",
                "device_id": device_id,
                "brightness": brightness,
                "status": "success"
            }
        
        else:
            raise ValueError(f"Type d'action inconnu: {action_type}")
    
    def _parse_time(self, time_str: str) -> time:
        """
        Parse une chaîne de temps au format "HH:MM".
        
        Args:
            time_str: Chaîne au format "HH:MM"
        
        Returns:
            Objet time
        """
        try:
            hour, minute = map(int, time_str.split(":"))
            return time(hour, minute)
        except Exception as e:
            logger.error(f"Erreur lors du parsing du temps '{time_str}': {e}")
            return time(0, 0)

