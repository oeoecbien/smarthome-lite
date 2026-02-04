"""
Entraînement du modèle Decision Tree pour classification de scénarios.

Ce script :
1. Charge les données d'entraînement depuis la base de données
2. Entraîne un Decision Tree Classifier
3. Évalue les performances
4. Sauvegarde le modèle au format pickle
"""

import os
import argparse
import joblib
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models import TrainingData
from app.database import Base


def load_training_data(db_session) -> tuple:
    """
    Charge les données d'entraînement depuis la base de données.
    
    Args:
        db_session: Session de base de données
    
    Returns:
        Tuple (X, y) où X sont les features et y les labels
    """
    training_data = db_session.query(TrainingData).all()
    
    if len(training_data) < 50:
        raise ValueError(
            f"Pas assez de données d'entraînement ({len(training_data)}). "
            f"Minimum requis: 50. Exécutez d'abord generate_data.py"
        )
    
    # Extraire les features et labels
    X = []
    y = []
    
    for data in training_data:
        X.append([
            data.hour,
            data.day_of_week,
            1 if data.presence_detected else 0,
            1 if data.light_on else 0
        ])
        y.append(data.scenario)
    
    return np.array(X), np.array(y)


def train_model(X_train, y_train, max_depth: int = 5) -> DecisionTreeClassifier:
    """
    Entraîne un Decision Tree Classifier.
    
    Args:
        X_train: Features d'entraînement
        y_train: Labels d'entraînement
        max_depth: Profondeur maximale de l'arbre
    
    Returns:
        Modèle entraîné
    """
    model = DecisionTreeClassifier(
        max_depth=max_depth,
        random_state=42,
        criterion="gini",
        min_samples_split=5,
        min_samples_leaf=2
    )
    
    model.fit(X_train, y_train)
    
    return model


def evaluate_model(model, X_test, y_test):
    """
    Évalue les performances du modèle.
    
    Args:
        model: Modèle entraîné
        X_test: Features de test
        y_test: Labels de test
    """
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print("\n" + "=" * 60)
    print("ÉVALUATION DU MODÈLE")
    print("=" * 60)
    print(f"Accuracy: {accuracy:.2%}")
    print()
    
    # Matrice de confusion
    print("Matrice de confusion:")
    cm = confusion_matrix(y_test, y_pred)
    scenario_names = ["Day", "Night", "Away", "Evening"]
    print("     ", " ".join(f"{name:>8}" for name in scenario_names))
    for i, row in enumerate(cm):
        print(f"{scenario_names[i]:>5}", " ".join(f"{val:>8}" for val in row))
    print()
    
    # Rapport de classification
    print("Rapport de classification:")
    print(classification_report(
        y_test,
        y_pred,
        target_names=scenario_names,
        digits=2
    ))
    
    return accuracy


def save_model(model, filepath: str, accuracy: float = None):
    """
    Sauvegarde le modèle au format pickle et les métriques en JSON.
    
    Args:
        model: Modèle à sauvegarder
        filepath: Chemin du fichier de sauvegarde
        accuracy: Précision sur le jeu de test (optionnel, pour metrics.json)
    """
    import json
    model_dir = os.path.dirname(filepath)
    os.makedirs(model_dir, exist_ok=True)
    
    joblib.dump(model, filepath)
    print(f"[OK] Modèle sauvegardé: {filepath}")
    
    if accuracy is not None:
        metrics_file = os.path.join(model_dir, "metrics.json")
        with open(metrics_file, "w") as f:
            json.dump({"accuracy": accuracy}, f, indent=2)
        print(f"[OK] Métriques sauvegardées: {metrics_file}")


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(description="Entraîne le modèle Decision Tree")
    parser.add_argument(
        "--max-depth",
        type=int,
        default=5,
        help="Profondeur maximale de l'arbre (par défaut: 5)"
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Proportion des données de test (par défaut: 0.2)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Chemin de sortie du modèle (par défaut: config.ml_model_path)"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("ENTRAÎNEMENT DU MODÈLE DECISION TREE")
    print("=" * 60)
    print(f"Profondeur maximale: {args.max_depth}")
    print(f"Proportion test: {args.test_size:.1%}")
    print()
    
    # Connexion à la base de données
    try:
        engine = create_engine(settings.database_url)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        # Charger les données
        print("Chargement des données d'entraînement...")
        X, y = load_training_data(db)
        print(f"[OK] {len(X)} échantillons chargés")
        
        # Statistiques
        unique, counts = np.unique(y, return_counts=True)
        scenario_names = {0: "Day", 1: "Night", 2: "Away", 3: "Evening"}
        print("\nRépartition des données:")
        for scenario, count in zip(unique, counts):
            print(f"  {scenario_names[scenario]}: {count} échantillons")
        print()
        
        # Division train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=args.test_size,
            random_state=42,
            stratify=y  # Maintenir la proportion des classes
        )
        
        print(f"Données d'entraînement: {len(X_train)} échantillons")
        print(f"Données de test: {len(X_test)} échantillons")
        print()
        
        # Entraînement
        print("Entraînement du modèle...")
        model = train_model(X_train, y_train, max_depth=args.max_depth)
        print("[OK] Modèle entraîné")
        
        # Évaluation
        accuracy = evaluate_model(model, X_test, y_test)
        
        # Sauvegarde (modèle + métriques pour l'API / frontend)
        output_path = args.output or settings.ml_model_path
        save_model(model, output_path, accuracy=accuracy)
        
        # Vérification de l'accuracy minimale
        if accuracy < 0.70:
            print("\n[ATTENTION]  ATTENTION: Accuracy < 70%")
            print("   Le modèle peut nécessiter plus de données d'entraînement.")
        else:
            print("\n[OK] Modèle conforme (accuracy >= 70%)")
        
        db.close()
        
    except Exception as e:
        print(f"\n[ERREUR] Erreur: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("\n" + "=" * 60)
    print("[OK] Entraînement terminé avec succès")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    exit(main())

