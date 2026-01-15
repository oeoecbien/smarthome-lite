"""
Génération de données synthétiques pour l'entraînement du modèle de régression.
Ce script génère un dataset pour prédire l'intensité lumineuse optimale.
"""

import random
import argparse
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models import TrainingData
from app.database import Base

# Configuration de la génération pour régression
# Target: intensité lumineuse optimale (0-100) selon le contexte
REGRESSION_RULES = {
    0: {  # Day
        "hour_range": (6, 18),
        "base_intensity": 40,
        "lux_factor": -0.1,  # Plus de lux = moins d'intensité nécessaire
        "presence_bonus": 10,
        "variation": 15
    },
    1: {  # Night
        "hour_range": (23, 6),
        "base_intensity": 25,
        "lux_factor": -0.15,
        "presence_bonus": 5,
        "variation": 10
    },
    2: {  # Away
        "hour_range": (9, 17),
        "base_intensity": 0,
        "lux_factor": 0,
        "presence_bonus": 0,
        "variation": 0
    },
    3: {  # Evening
        "hour_range": (18, 23),
        "base_intensity": 60,
        "lux_factor": -0.12,
        "presence_bonus": 15,
        "variation": 20
    }
}


def generate_regression_sample(
    scenario: int,
    hour: int,
    day_of_week: int,
    lux_value: float,
    presence_detected: bool
) -> dict:
    """
    Génère un échantillon synthétique pour la régression.
    
    Args:
        scenario: Numéro du scénario (0-3)
        hour: Heure actuelle (0-23)
        day_of_week: Jour de la semaine (0-6)
        lux_value: Valeur de luminosité ambiante en lux
        presence_detected: Présence détectée
        
    Returns:
        Dict avec features et target (intensity)
    """
    rules = REGRESSION_RULES[scenario]
    
    # Calculer l'intensité de base
    base_intensity = rules["base_intensity"]
    
    # Ajustement selon la luminosité ambiante
    lux_adjustment = lux_value * rules["lux_factor"]
    
    # Bonus si présence détectée
    presence_adjustment = rules["presence_bonus"] if presence_detected else 0
    
    # Calculer l'intensité cible
    target_intensity = base_intensity + lux_adjustment + presence_adjustment
    
    # Ajouter de la variation aléatoire
    variation = random.uniform(-rules["variation"], rules["variation"])
    target_intensity += variation
    
    # Clamp entre 0 et 100
    target_intensity = max(0, min(100, int(target_intensity)))
    
    return {
        "hour": hour,
        "day_of_week": day_of_week,
        "lux_value": round(lux_value, 2),
        "presence_detected": presence_detected,
        "scenario": scenario,
        "intensity": target_intensity
    }


def generate_regression_dataset(samples_per_scenario: int = 200) -> list:
    """
    Génère un dataset équilibré pour la régression.
    
    Args:
        samples_per_scenario: Nombre d'échantillons par scénario
        
    Returns:
        Liste de dictionnaires représentant les échantillons
    """
    dataset = []
    
    for scenario in range(4):  # 4 scénarios
        rules = REGRESSION_RULES[scenario]
        hour_start, hour_end = rules["hour_range"]
        
        for _ in range(samples_per_scenario):
            # Générer l'heure selon la plage du scénario
            if hour_start > hour_end:  # Plage qui traverse minuit
                if random.random() < 0.5:
                    hour = random.randint(hour_start, 23)
                else:
                    hour = random.randint(0, hour_end)
            else:
                hour = random.randint(hour_start, hour_end)
            
            # Jour de la semaine
            day_of_week = random.randint(0, 6)
            
            # Luminosité ambiante (selon scénario)
            if scenario == 0:  # Day
                lux_value = random.uniform(200, 800)
            elif scenario == 1:  # Night
                lux_value = random.uniform(0, 50)
            elif scenario == 2:  # Away
                lux_value = random.uniform(100, 600)
            else:  # Evening
                lux_value = random.uniform(50, 300)
            
            # Présence
            presence_detected = random.random() < 0.7 if scenario != 2 else random.random() < 0.1
            
            # Générer l'échantillon
            sample = generate_regression_sample(
                scenario, hour, day_of_week, lux_value, presence_detected
            )
            dataset.append(sample)
    
    # Mélanger le dataset
    random.shuffle(dataset)
    
    return dataset


def save_to_database(dataset: list, db: Session):
    """
    Sauvegarde le dataset en base de données.
    Note: On utilise TrainingData mais on ajoute une colonne intensity si nécessaire.
    Pour l'instant, on stocke dans un format compatible.
    """
    print(f"Insertion de {len(dataset)} échantillons de régression en base de données...")
    
    # Note: On pourrait créer une table séparée RegressionTrainingData
    # Pour l'instant, on utilise TrainingData avec scenario comme proxy
    # et on stocke intensity dans un champ dérivé ou une table séparée
    
    # Option 1: Créer une nouvelle table (nécessite migration)
    # Option 2: Utiliser TrainingData et ajouter intensity via une relation
    # Option 3: Stocker dans un fichier JSON séparé
    
    # Pour l'instant, on va créer une table simple ou utiliser un fichier
    # On va sauvegarder dans un fichier JSON pour l'entraînement
    import json
    import os
    
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)
    
    output_file = os.path.join(data_dir, "regression_training_data.json")
    
    with open(output_file, "w") as f:
        json.dump(dataset, f, indent=2)
    
    print(f"[OK] {len(dataset)} échantillons sauvegardés dans {output_file}")
    print("Note: Les données sont sauvegardées dans un fichier JSON pour l'entraînement")


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(
        description="Génère des données d'entraînement pour la régression"
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=800,
        help="Nombre total d'échantillons à générer (par défaut: 800)"
    )
    
    args = parser.parse_args()
    
    # Calculer le nombre d'échantillons par scénario
    samples_per_scenario = max(1, args.samples // 4)
    total_samples = samples_per_scenario * 4
    
    print("=" * 60)
    print("GÉNÉRATION DE DONNÉES D'ENTRAÎNEMENT - RÉGRESSION")
    print("=" * 60)
    print(f"Nombre total d'échantillons: {total_samples}")
    print(f"Par scénario: {samples_per_scenario}")
    print()
    
    # Générer le dataset
    dataset = generate_regression_dataset(samples_per_scenario)
    
    # Afficher les statistiques
    scenario_counts = {}
    intensity_stats = {}
    
    for sample in dataset:
        scenario = sample["scenario"]
        scenario_counts[scenario] = scenario_counts.get(scenario, 0) + 1
        
        if scenario not in intensity_stats:
            intensity_stats[scenario] = []
        intensity_stats[scenario].append(sample["intensity"])
    
    print("Répartition par scénario:")
    scenario_names = {0: "Day", 1: "Night", 2: "Away", 3: "Evening"}
    for scenario, count in sorted(scenario_counts.items()):
        intensities = intensity_stats[scenario]
        avg_intensity = sum(intensities) / len(intensities)
        min_intensity = min(intensities)
        max_intensity = max(intensities)
        print(
            f"  {scenario_names[scenario]} ({scenario}): {count} échantillons, "
            f"intensité moyenne: {avg_intensity:.1f}% (min: {min_intensity}, max: {max_intensity})"
        )
    print()
    
    # Sauvegarder
    try:
        save_to_database(dataset, None)
    except Exception as e:
        print(f"[ERREUR] Erreur lors de la sauvegarde: {e}")
    
    print()
    print("=" * 60)
    print("[OK] Génération terminée")
    print("=" * 60)


if __name__ == "__main__":
    main()
