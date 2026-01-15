"""
Module de contrôle pour une lampe Z-Wave
Gère l'allumage, l'extinction et le dimming
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from zwave_controller import ZWaveController

logger = logging.getLogger(__name__)


class ZWaveLamp:
    """Contrôleur pour une lampe Z-Wave"""
    
    # Command Classes Z-Wave courantes pour les lampes
    SWITCH_BINARY = "37"  # Interrupteur simple On/Off
    SWITCH_MULTILEVEL = "38"  # Variateur (dimming)
    
    def __init__(self, node_id: int, controller: Optional[ZWaveController] = None, 
                 base_url: str = "http://localhost:8091"):
        """
        Initialise le contrôleur de lampe Z-Wave
        
        Args:
            node_id: ID du nœud Z-Wave de la lampe
            controller: Instance de ZWaveController (créée si None)
            base_url: URL de base de ZwaveJS2MQTT
        """
        self.node_id = node_id
        self.controller = controller or ZWaveController(base_url)
        self._value_ids = {}
        self._detect_capabilities()
    
    def _detect_capabilities(self):
        """Détecte les capacités de la lampe (On/Off, Dimming)"""
        node = self.controller.get_node(self.node_id)
        if not node:
            logger.warning(f"Nœud {self.node_id} non trouvé")
            return
        
        values = node.get("values", {})
        
        # Chercher les commandes disponibles
        for value_id, value_data in values.items():
            command_class = value_data.get("commandClass")
            property_name = value_data.get("property")
            
            # Interrupteur binaire (On/Off)
            if command_class == self.SWITCH_BINARY and property_name == "currentValue":
                self._value_ids["switch"] = value_id
                logger.info(f"Lampe {self.node_id}: Interrupteur détecté")
            
            # Variateur (Dimming)
            elif command_class == self.SWITCH_MULTILEVEL:
                if property_name == "targetValue":
                    self._value_ids["dim_target"] = value_id
                elif property_name == "currentValue":
                    self._value_ids["dim_current"] = value_id
                    logger.info(f"Lampe {self.node_id}: Variateur détecté")
    
    def is_on(self) -> Optional[bool]:
        """
        Vérifie si la lampe est allumée
        
        Returns:
            True si allumée, False si éteinte, None si erreur
        """
        if "switch" in self._value_ids:
            value = self.controller.get_value(self.node_id, self._value_ids["switch"])
            return value == 255 or value is True
        elif "dim_current" in self._value_ids:
            value = self.controller.get_value(self.node_id, self._value_ids["dim_current"])
            return value is not None and value > 0
        return None
    
    def turn_on(self) -> bool:
        """
        Allume la lampe
        
        Returns:
            True si succès, False sinon
        """
        if "switch" in self._value_ids:
            return self.controller.set_value(self.node_id, self._value_ids["switch"], True)
        elif "dim_target" in self._value_ids:
            # Allumer à 100% pour un variateur
            return self.controller.set_value(self.node_id, self._value_ids["dim_target"], 99)
        else:
            logger.error(f"Impossible d'allumer la lampe {self.node_id}: aucune commande disponible")
            return False
    
    def turn_off(self) -> bool:
        """
        Éteint la lampe
        
        Returns:
            True si succès, False sinon
        """
        if "switch" in self._value_ids:
            return self.controller.set_value(self.node_id, self._value_ids["switch"], False)
        elif "dim_target" in self._value_ids:
            return self.controller.set_value(self.node_id, self._value_ids["dim_target"], 0)
        else:
            logger.error(f"Impossible d'éteindre la lampe {self.node_id}: aucune commande disponible")
            return False
    
    def set_brightness(self, level: int) -> bool:
        """
        Définit le niveau de luminosité (0-100)
        
        Args:
            level: Niveau de luminosité (0-100)
            
        Returns:
            True si succès, False sinon
        """
        if "dim_target" not in self._value_ids:
            logger.warning(f"Lampe {self.node_id} ne supporte pas le dimming")
            return False
        
        # Z-Wave utilise 0-99 pour le dimming
        zwave_level = max(0, min(99, int(level * 0.99)))
        return self.controller.set_value(self.node_id, self._value_ids["dim_target"], zwave_level)
    
    def get_brightness(self) -> Optional[int]:
        """
        Récupère le niveau de luminosité actuel (0-100)
        
        Returns:
            Niveau de luminosité (0-100) ou None
        """
        if "dim_current" in self._value_ids:
            value = self.controller.get_value(self.node_id, self._value_ids["dim_current"])
            if value is not None:
                # Convertir de 0-99 à 0-100
                return int((value / 99) * 100)
        return None
    
    def toggle(self) -> bool:
        """
        Bascule l'état de la lampe (allume si éteinte, éteint si allumée)
        
        Returns:
            True si succès, False sinon
        """
        current_state = self.is_on()
        if current_state is None:
            return False
        return self.turn_off() if current_state else self.turn_on()
    
    def is_available(self) -> bool:
        """
        Vérifie si la lampe est disponible (connectée au réseau)
        
        Returns:
            True si disponible
        """
        node = self.controller.get_node(self.node_id)
        if not node:
            return False
        return node.get("status", {}).get("status", "Unknown") == "Alive"

