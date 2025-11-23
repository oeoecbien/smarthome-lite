"""
Génération de données synthétiques pour l'entraînement du modèle de classification.

Ce script génère un dataset équilibré de 500 échantillons minimum pour entraîner
un Decision Tree Classifier capable de classer les scénarios :
- 0: Day (journée)
- 1: Night (nuit)
- 2: Away (absence)
- 3: Evening (soirée)
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

# Configuration de la génération
SCENARIO_RULES = {
    0: {  # Day
        "hour_range": (6, 18),
        "presence_probability": 0.7,
        "light_on_probability": 0.6
    },
    1: {  # Night
        "hour_range": (23, 6),  # 23h-6h (traverse minuit)
        "presence_probability": 0.2,
        "light_on_probability": 0.3
    },
    2: {  # Away
        "hour_range": (9, 17),
        "presence_probability": 0.1,
        "light_on_probability": 0.1
    },
    3: {  # Evening
        "hour_range": (18, 23),
        "presence_probability": 0.9,
        "light_on_probability": 0.8
    }
}


def generate_sample(scenario: int) -> dict:
    """
    Génère un échantillon synthétique pour un scénario donné.
    
    Args:
        scenario: Numéro du scénario (0-3)
    
    Returns:
        Dict avec hour, day_of_week, presence_detected, light_on, scenario
    """
    rules = SCENARIO_RULES[scenario]
    
    # Générer l'heure selon la plage du scénario
    hour_start, hour_end = rules["hour_range"]
    
    if hour_start > hour_end:  # Plage qui traverse minuit (ex: 23-6)
        # Générer entre 23h et 23h59 OU entre 0h et 6h
        if random.random() < 0.5:
            hour = random.randint(hour_start, 23)
        else:
            hour = random.randint(0, hour_end)
    else:
        hour = random.randint(hour_start, hour_end)
    
    # Jour de la semaine (0=Lundi, 6=Dimanche)
    day_of_week = random.randint(0, 6)
    
    # Présence selon probabilité du scénario
    presence_detected = random.random() < rules["presence_probability"]
    
    # Lumière selon probabilité du scénario
    light_on = random.random() < rules["light_on_probability"]
    
    return {
        "hour": hour,
        "day_of_week": day_of_week,
        "presence_detected": presence_detected,
        "light_on": light_on,
        "scenario": scenario
    }


def generate_dataset(samples_per_scenario: int = 125) -> list:
    """
    Génère un dataset équilibré.
    
    Args:
        samples_per_scenario: Nombre d'échantillons par scénario
    
    Returns:
        Liste de dictionnaires représentant les échantillons
    """
    dataset = []
    
    for scenario in range(4):  # 4 scénarios
        for _ in range(samples_per_scenario):
            sample = generate_sample(scenario)
            dataset.append(sample)
    
    # Mélanger le dataset
    random.shuffle(dataset)
    
    return dataset


def save_to_database(dataset: list, db: Session):
    """
    Sauvegarde le dataset en base de données.
    
    Args:
        dataset: Liste d'échantillons
        db: Session de base de données
    """
    print(f"Insertion de {len(dataset)} échantillons en base de données...")
    
    # Supprimer les anciennes données (optionnel)
    db.query(TrainingData).delete()
    db.commit()
    
    # Insérer les nouveaux échantillons
    for sample in dataset:
        training_data = TrainingData(
            hour=sample["hour"],
            day_of_week=sample["day_of_week"],
            presence_detected=sample["presence_detected"],
            light_on=sample["light_on"],
            scenario=sample["scenario"]
        )
        db.add(training_data)
    
    db.commit()
    print(f"[OK] {len(dataset)} échantillons insérés avec succès")


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(description="Génère des données d'entraînement synthétiques")
    parser.add_argument(
        "--samples",
        type=int,
        default=500,
        help="Nombre total d'échantillons à générer (par défaut: 500)"
    )
    parser.add_argument(
        "--no-db",
        action="store_true",
        help="Ne pas sauvegarder en base de données (afficher uniquement)"
    )
    
    args = parser.parse_args()
    
    # Calculer le nombre d'échantillons par scénario
    samples_per_scenario = max(1, args.samples // 4)
    total_samples = samples_per_scenario * 4
    
    print("=" * 60)
    print("GÉNÉRATION DE DONNÉES D'ENTRAÎNEMENT")
    print("=" * 60)
    print(f"Nombre total d'échantillons: {total_samples}")
    print(f"Par scénario: {samples_per_scenario}")
    print()
    
    # Générer le dataset
    dataset = generate_dataset(samples_per_scenario)
    
    # Afficher les statistiques
    scenario_counts = {}
    for sample in dataset:
        scenario = sample["scenario"]
        scenario_counts[scenario] = scenario_counts.get(scenario, 0) + 1
    
    print("Répartition par scénario:")
    scenario_names = {0: "Day", 1: "Night", 2: "Away", 3: "Evening"}
    for scenario, count in sorted(scenario_counts.items()):
        print(f"  {scenario_names[scenario]} ({scenario}): {count} échantillons")
    print()
    
    # Sauvegarder en base de données si demandé
    if not args.no_db:
        try:
            engine = create_engine(settings.database_url)
            Base.metadata.create_all(engine)
            SessionLocal = sessionmaker(bind=engine)
            db = SessionLocal()
            
            save_to_database(dataset, db)
            db.close()
        except Exception as e:
            print(f"[ERREUR] Erreur lors de la sauvegarde en base: {e}")
            print("Les données ont été générées mais non sauvegardées.")
    else:
        print("Mode --no-db: données non sauvegardées")
        print(f"Premiers échantillons:")
        for i, sample in enumerate(dataset[:5]):
            print(f"  {i+1}. {sample}")
    
    print()
    print("=" * 60)
    print("[OK] Génération terminée")
    print("=" * 60)


if __name__ == "__main__":
    main()

