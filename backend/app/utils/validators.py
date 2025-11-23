"""
Fonctions de validation métier pour l'application SmartHome.

Ce module contient des validateurs personnalisés qui complètent
les validations Pydantic en ajoutant de la logique métier.

Utilisations:
    - Validation de disponibilité des GPIO pins
    - Validation de cohérence des règles d'automatisation
    - Validation de formats spécifiques (heures, dates)
"""
from typing import Optional, Tuple
from datetime import time
import re
from sqlalchemy.orm import Session

from app.models.device import Device
from app.models.raspberry_pi import RaspberryPi


# ========== Validation des GPIO Pins ==========

def validate_gpio_pin_available(
    db: Session,
    raspberry_pi_id: int,
    gpio_pin: int,
    exclude_device_id: Optional[int] = None
) -> Tuple[bool, Optional[str]]:
    """
    Vérifie qu'un GPIO pin est disponible sur un Raspberry Pi.
    
    Règles de validation:
        1. Le Raspberry Pi existe
        2. Le GPIO pin est dans la plage valide (0-27 pour GPIO standards)
        3. Aucun autre appareil n'utilise ce pin sur ce Raspberry Pi
    
    Args:
        db (Session): Session SQLAlchemy
        raspberry_pi_id (int): ID du Raspberry Pi
        gpio_pin (int): Numéro du GPIO à valider
        exclude_device_id (int, optional): ID d'un appareil à exclure de la vérification
            (utile lors de la mise à jour d'un appareil existant)
            
    Returns:
        tuple[bool, str | None]: (is_valid, error_message)
            - (True, None) si le pin est disponible
            - (False, "message d'erreur") si le pin n'est pas disponible
            
    Exemple:
        >>> is_valid, error = validate_gpio_pin_available(db, raspberry_pi_id=1, gpio_pin=17)
        >>> if not is_valid:
        ...     raise HTTPException(status_code=400, detail=error)
        
        >>> # Lors d'une mise à jour (exclure l'appareil en cours de modification)
        >>> is_valid, error = validate_gpio_pin_available(
        ...     db, raspberry_pi_id=1, gpio_pin=17, exclude_device_id=5
        ... )
    """
    # Vérification 1: Le Raspberry Pi existe
    rpi = db.query(RaspberryPi).filter(RaspberryPi.id == raspberry_pi_id).first()
    if not rpi:
        return False, f"Raspberry Pi avec ID {raspberry_pi_id} introuvable"
    
    # Vérification 2: Plage de GPIO valide
    # GPIO standards: 0-27 (pins physiques 1-40, mais certains réservés)
    # Voir: https://pinout.xyz/
    valid_gpio_pins = list(range(0, 28))  # 0 à 27 inclus
    if gpio_pin not in valid_gpio_pins:
        return False, f"GPIO pin {gpio_pin} invalide. Plage autorisée: 0-27"
    
    # Vérification 3: Pin déjà utilisé par un autre appareil
    query = db.query(Device).filter(
        Device.raspberry_pi_id == raspberry_pi_id,
        Device.gpio_pin == gpio_pin
    )
    
    # Exclure l'appareil en cours de modification (cas de la mise à jour)
    if exclude_device_id:
        query = query.filter(Device.id != exclude_device_id)
    
    existing_device = query.first()
    if existing_device:
        return False, (
            f"GPIO pin {gpio_pin} déjà utilisé par l'appareil "
            f"'{existing_device.name}' (ID: {existing_device.id})"
        )
    
    # Toutes les validations passées
    return True, None


# ========== Validation des valeurs de luminosité ==========

def validate_brightness_range(brightness: int) -> Tuple[bool, Optional[str]]:
    """
    Vérifie qu'une valeur de luminosité est dans la plage valide (0-100).
    
    Cette validation complète celle de Pydantic en ajoutant des messages
    d'erreur plus explicites pour l'utilisateur final.
    
    Args:
        brightness (int): Valeur de luminosité à valider
        
    Returns:
        tuple[bool, str | None]: (is_valid, error_message)
        
    Exemple:
        >>> is_valid, error = validate_brightness_range(75)
        >>> print(is_valid)
        True
        
        >>> is_valid, error = validate_brightness_range(150)
        >>> print(error)
        L'intensité lumineuse doit être entre 0 et 100 (reçu: 150)
    """
    if not 0 <= brightness <= 100:
        return False, f"L'intensité lumineuse doit être entre 0 et 100 (reçu: {brightness})"
    return True, None


def calculate_brightness_step(current: int, target: int, max_step: int = 10) -> int:
    """
    Calcule un pas progressif pour transition douce de luminosité.
    
    Utilisé par le Smart Dimming pour éviter des changements brusques.
    
    Args:
        current (int): Intensité actuelle (0-100)
        target (int): Intensité cible (0-100)
        max_step (int): Pas maximal par ajustement (défaut: 10)
        
    Returns:
        int: Prochaine valeur de luminosité à appliquer
        
    Exemple:
        >>> # Transition de 100% à 50%
        >>> step1 = calculate_brightness_step(100, 50)
        >>> print(step1)
        90  # Diminution de 10%
        
        >>> # Si la différence est < max_step, on atteint directement la cible
        >>> step2 = calculate_brightness_step(55, 50)
        >>> print(step2)
        50
    """
    diff = target - current
    
    # Si la différence est inférieure au pas maximal, on atteint directement la cible
    if abs(diff) <= max_step:
        return target
    
    # Sinon, on avance par pas progressif
    if diff > 0:
        return current + max_step
    else:
        return current - max_step


# ========== Validation des formats de temps ==========

def validate_time_format(time_str: str) -> Tuple[bool, Optional[str]]:
    """
    Valide le format d'une chaîne de temps (HH:MM).
    
    Args:
        time_str (str): Chaîne de temps au format "HH:MM"
        
    Returns:
        tuple[bool, str | None]: (is_valid, error_message)
        
    Exemple:
        >>> is_valid, error = validate_time_format("08:30")
        >>> print(is_valid)
        True
        
        >>> is_valid, error = validate_time_format("25:00")
        >>> print(error)
        Format de temps invalide: heure doit être entre 0 et 23
    """
    # Vérification du format avec regex
    pattern = r"^([0-1]?[0-9]|2[0-3]):([0-5][0-9])$"
    if not re.match(pattern, time_str):
        return False, (
            f"Format de temps invalide: '{time_str}'. "
            "Format attendu: HH:MM (ex: 08:30, 14:45)"
        )
    
    # Validation supplémentaire des valeurs
    try:
        hours, minutes = map(int, time_str.split(":"))
        
        if not 0 <= hours <= 23:
            return False, f"Format de temps invalide: heure doit être entre 0 et 23 (reçu: {hours})"
        
        if not 0 <= minutes <= 59:
            return False, f"Format de temps invalide: minutes doivent être entre 0 et 59 (reçu: {minutes})"
        
        # Conversion en objet time pour validation finale
        time(hours, minutes)
        
    except ValueError as e:
        return False, f"Format de temps invalide: {str(e)}"
    
    return True, None


def parse_time_string(time_str: str) -> Optional[time]:
    """
    Parse une chaîne de temps en objet Python time.
    
    Args:
        time_str (str): Chaîne au format "HH:MM"
        
    Returns:
        time | None: Objet time si valide, None sinon
        
    Exemple:
        >>> t = parse_time_string("14:30")
        >>> print(t.hour, t.minute)
        14 30
    """
    is_valid, _ = validate_time_format(time_str)
    if not is_valid:
        return None
    
    hours, minutes = map(int, time_str.split(":"))
    return time(hours, minutes)


def is_time_between(current: time, start: time, end: time) -> bool:
    """
    Vérifie si un temps est compris dans un intervalle.
    
    Gère correctement les intervalles qui traversent minuit.
    
    Args:
        current (time): Temps à vérifier
        start (time): Début de l'intervalle
        end (time): Fin de l'intervalle
        
    Returns:
        bool: True si current est dans [start, end]
        
    Exemple:
        >>> from datetime import time
        >>> current = time(14, 30)
        >>> start = time(8, 0)
        >>> end = time(18, 0)
        >>> is_time_between(current, start, end)
        True
        
        >>> # Intervalle traversant minuit (22:00 - 06:00)
        >>> night_time = time(2, 0)
        >>> is_time_between(night_time, time(22, 0), time(6, 0))
        True
    """
    if start <= end:
        # Intervalle normal (ex: 08:00 - 18:00)
        return start <= current <= end
    else:
        # Intervalle traversant minuit (ex: 22:00 - 06:00)
        return current >= start or current <= end


# ========== Validation des règles d'automatisation ==========

def validate_rule_condition(condition: dict) -> Tuple[bool, Optional[str]]:
    """
    Valide la structure d'une condition de règle d'automatisation.
    
    Structure attendue:
        {
            "type": "AND" | "OR" | "time" | "presence" | "light",
            "operator": "<" | ">" | "=" | "between",  # optionnel
            "value": any,  # obligatoire
            "conditions": [...]  # pour AND/OR
        }
    
    Args:
        condition (dict): Condition à valider
        
    Returns:
        tuple[bool, str | None]: (is_valid, error_message)
        
    Exemple:
        >>> condition = {
        ...     "type": "AND",
        ...     "conditions": [
        ...         {"type": "time", "operator": "between", "value": ["08:00", "18:00"]},
        ...         {"type": "presence", "value": True}
        ...     ]
        ... }
        >>> is_valid, error = validate_rule_condition(condition)
        >>> print(is_valid)
        True
    """
    # Vérification des champs obligatoires
    if "type" not in condition:
        return False, "Champ 'type' manquant dans la condition"
    
    condition_type = condition["type"]
    allowed_types = ["AND", "OR", "time", "presence", "light", "scenario"]
    
    if condition_type not in allowed_types:
        return False, f"Type de condition invalide: {condition_type}. Types autorisés: {', '.join(allowed_types)}"
    
    # Validation spécifique selon le type
    if condition_type in ["AND", "OR"]:
        # Les conditions composées doivent avoir un tableau de sous-conditions
        if "conditions" not in condition:
            return False, f"Condition de type {condition_type} doit contenir un champ 'conditions'"
        
        if not isinstance(condition["conditions"], list):
            return False, f"Le champ 'conditions' doit être un tableau"
        
        if len(condition["conditions"]) == 0:
            return False, f"Condition de type {condition_type} doit contenir au moins une sous-condition"
        
        # Validation récursive des sous-conditions
        for i, sub_condition in enumerate(condition["conditions"]):
            is_valid, error = validate_rule_condition(sub_condition)
            if not is_valid:
                return False, f"Sous-condition {i+1}: {error}"
    
    else:
        # Les conditions simples doivent avoir une valeur
        if "value" not in condition:
            return False, f"Condition de type {condition_type} doit contenir un champ 'value'"
        
        # Validation spécifique par type
        if condition_type == "time":
            operator = condition.get("operator")
            if operator == "between":
                # Format attendu: ["HH:MM", "HH:MM"]
                value = condition["value"]
                if not isinstance(value, list) or len(value) != 2:
                    return False, "Condition 'time between' doit avoir 2 valeurs: [start, end]"
                
                for time_str in value:
                    is_valid, error = validate_time_format(time_str)
                    if not is_valid:
                        return False, f"Temps invalide dans condition: {error}"
            
            elif operator in ["<", ">", "="]:
                # Format attendu: "HH:MM"
                is_valid, error = validate_time_format(condition["value"])
                if not is_valid:
                    return False, f"Temps invalide dans condition: {error}"
            
            else:
                return False, f"Opérateur invalide pour condition time: {operator}"
        
        elif condition_type == "presence":
            # Valeur attendue: boolean
            if not isinstance(condition["value"], bool):
                return False, "Condition 'presence' doit avoir une valeur booléenne (true/false)"
        
        elif condition_type == "light":
            # Valeur attendue: nombre (lux) + opérateur
            if "operator" not in condition:
                return False, "Condition 'light' doit spécifier un opérateur (<, >, =)"
            
            if not isinstance(condition["value"], (int, float)):
                return False, "Condition 'light' doit avoir une valeur numérique (lux)"
    
    return True, None


def validate_rule_action(action: dict, db: Session) -> Tuple[bool, Optional[str]]:
    """
    Valide la structure d'une action de règle d'automatisation.
    
    Structure attendue:
        {
            "device_id": int,
            "action": "turn_on" | "turn_off" | "set_brightness",
            "brightness": int  # optionnel, requis pour set_brightness
        }
    
    Args:
        action (dict): Action à valider
        db (Session): Session SQLAlchemy pour vérifier l'existence de l'appareil
        
    Returns:
        tuple[bool, str | None]: (is_valid, error_message)
    """
    # Vérification des champs obligatoires
    if "device_id" not in action:
        return False, "Champ 'device_id' manquant dans l'action"
    
    if "action" not in action:
        return False, "Champ 'action' manquant"
    
    # Validation du type d'action
    allowed_actions = ["turn_on", "turn_off", "set_brightness"]
    if action["action"] not in allowed_actions:
        return False, f"Action invalide: {action['action']}. Actions autorisées: {', '.join(allowed_actions)}"
    
    # Vérification de l'existence de l'appareil
    device = db.query(Device).filter(Device.id == action["device_id"]).first()
    if not device:
        return False, f"Appareil avec ID {action['device_id']} introuvable"
    
    # Validation spécifique pour set_brightness
    if action["action"] == "set_brightness":
        if "brightness" not in action:
            return False, "Action 'set_brightness' doit spécifier un champ 'brightness'"
        
        is_valid, error = validate_brightness_range(action["brightness"])
        if not is_valid:
            return False, error
        
        # Vérifier que l'appareil supporte le dimming
        if device.type not in ["light", "dimmer"]:
            return False, f"L'appareil '{device.name}' (type: {device.type}) ne supporte pas le réglage de luminosité"
    
    return True, None
