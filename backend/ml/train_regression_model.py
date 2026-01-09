"""
Entraînement du modèle Random Forest Regressor pour prédiction d'intensité lumineuse.
"""

import os
import argparse
import json
import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler

from app.config import settings


def load_regression_data(data_file: str) -> tuple:
    """
    Charge les données d'entraînement depuis le fichier JSON.
    
    Args:
        data_file: Chemin vers le fichier JSON
        
    Returns:
        Tuple (X, y) où X sont les features et y les targets (intensity)
    """
    if not os.path.exists(data_file):
        raise FileNotFoundError(
            f"Fichier de données non trouvé: {data_file}\n"
            f"Exécutez d'abord generate_regression_data.py"
        )
    
    with open(data_file, "r") as f:
        dataset = json.load(f)
    
    if len(dataset) < 100:
        raise ValueError(
            f"Pas assez de données d'entraînement ({len(dataset)}). "
            f"Minimum requis: 100. Exécutez d'abord generate_regression_data.py avec --samples 400"
        )
    
    # Extraire les features et targets
    X = []
    y = []
    
    for sample in dataset:
        X.append([
            sample["hour"],
            sample["day_of_week"],
            sample["lux_value"],
            1 if sample["presence_detected"] else 0,
            sample["scenario"]
        ])
        y.append(sample["intensity"])
    
    return np.array(X), np.array(y)


def train_model(X_train, y_train, n_estimators: int = 100, max_depth: int = 10) -> RandomForestRegressor:
    """
    Entraîne un Random Forest Regressor.
    
    Args:
        X_train: Features d'entraînement
        y_train: Targets d'entraînement
        n_estimators: Nombre d'arbres
        max_depth: Profondeur maximale
        
    Returns:
        Modèle entraîné
    """
    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1  # Utiliser tous les CPU disponibles
    )
    
    model.fit(X_train, y_train)
    
    return model


def evaluate_model(model, X_test, y_test):
    """
    Évalue les performances du modèle.
    
    Args:
        model: Modèle entraîné
        X_test: Features de test
        y_test: Targets de test
        
    Returns:
        Dict avec les métriques
    """
    y_pred = model.predict(X_test)
    
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    
    print("\n" + "=" * 60)
    print("ÉVALUATION DU MODÈLE DE RÉGRESSION")
    print("=" * 60)
    print(f"MAE (Mean Absolute Error): {mae:.2f}%")
    print(f"RMSE (Root Mean Squared Error): {rmse:.2f}%")
    print(f"R² Score: {r2:.4f}")
    print()
    
    # Statistiques des erreurs
    errors = np.abs(y_test - y_pred)
    print(f"Erreur moyenne: {np.mean(errors):.2f}%")
    print(f"Erreur médiane: {np.median(errors):.2f}%")
    print(f"Erreur max: {np.max(errors):.2f}%")
    print(f"Erreur min: {np.min(errors):.2f}%")
    print()
    
    # Distribution des erreurs
    print("Distribution des erreurs:")
    print(f"  < 5%:   {np.sum(errors < 5) / len(errors) * 100:.1f}%")
    print(f"  < 10%:  {np.sum(errors < 10) / len(errors) * 100:.1f}%")
    print(f"  < 20%:  {np.sum(errors < 20) / len(errors) * 100:.1f}%")
    print(f"  >= 20%: {np.sum(errors >= 20) / len(errors) * 100:.1f}%")
    print()
    
    return {
        "mae": float(mae),
        "rmse": float(rmse),
        "r2": float(r2),
        "mean_error": float(np.mean(errors)),
        "median_error": float(np.median(errors))
    }


def save_model(model, filepath: str, metrics: dict = None):
    """
    Sauvegarde le modèle au format joblib.
    
    Args:
        model: Modèle à sauvegarder
        filepath: Chemin du fichier de sauvegarde
        metrics: Métriques à sauvegarder
    """
    # Créer le répertoire s'il n'existe pas
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Sauvegarder le modèle
    joblib.dump(model, filepath)
    print(f"[OK] Modèle sauvegardé: {filepath}")
    
    # Sauvegarder les métriques
    if metrics:
        metrics_file = filepath.replace(".joblib", "_metrics.json")
        with open(metrics_file, "w") as f:
            json.dump(metrics, f, indent=2)
        print(f"[OK] Métriques sauvegardées: {metrics_file}")


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(description="Entraîne le modèle Random Forest Regressor")
    parser.add_argument(
        "--n-estimators",
        type=int,
        default=100,
        help="Nombre d'arbres (par défaut: 100)"
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=10,
        help="Profondeur maximale (par défaut: 10)"
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Proportion des données de test (par défaut: 0.2)"
    )
    parser.add_argument(
        "--data-file",
        type=str,
        default=None,
        help="Chemin vers le fichier de données (par défaut: ml/data/regression_training_data.json)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Chemin de sortie du modèle (par défaut: ml/models/regression_model.joblib)"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("ENTRAÎNEMENT DU MODÈLE RANDOM FOREST REGRESSOR")
    print("=" * 60)
    print(f"Nombre d'arbres: {args.n_estimators}")
    print(f"Profondeur maximale: {args.max_depth}")
    print(f"Proportion test: {args.test_size:.1%}")
    print()
    
    # Chemin du fichier de données
    if args.data_file:
        data_file = args.data_file
    else:
        data_file = os.path.join(
            os.path.dirname(__file__),
            "data",
            "regression_training_data.json"
        )
    
    # Charger les données
    print("Chargement des données d'entraînement...")
    X, y = load_regression_data(data_file)
    print(f"[OK] {len(X)} échantillons chargés")
    print(f"Features: {X.shape[1]} (hour, day_of_week, lux_value, presence_detected, scenario)")
    print(f"Target range: {np.min(y):.0f}% - {np.max(y):.0f}%")
    print(f"Target mean: {np.mean(y):.1f}%")
    print()
    
    # Division train/test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=args.test_size,
        random_state=42
    )
    
    print(f"Données d'entraînement: {len(X_train)} échantillons")
    print(f"Données de test: {len(X_test)} échantillons")
    print()
    
    # Validation croisée
    print("Validation croisée (5 folds)...")
    model_temp = RandomForestRegressor(
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        random_state=42,
        n_jobs=-1
    )
    cv_scores = cross_val_score(model_temp, X_train, y_train, cv=5, scoring='r2')
    print(f"R² Score (CV): {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
    print()
    
    # Entraînement
    print("Entraînement du modèle...")
    model = train_model(X_train, y_train, args.n_estimators, args.max_depth)
    print("[OK] Modèle entraîné")
    print()
    
    # Évaluation
    metrics = evaluate_model(model, X_test, y_test)
    
    # Importance des features
    print("Importance des features:")
    feature_names = ["hour", "day_of_week", "lux_value", "presence_detected", "scenario"]
    importances = model.feature_importances_
    for name, importance in zip(feature_names, importances):
        print(f"  {name}: {importance:.4f}")
    print()
    
    # Sauvegarde
    if args.output:
        output_path = args.output
    else:
        output_path = os.path.join(
            os.path.dirname(__file__),
            "models",
            "regression_model.joblib"
        )
    
    save_model(model, output_path, metrics)
    
    # Vérification de la qualité
    if metrics["r2"] < 0.70:
        print("\n[ATTENTION] R² Score < 0.70")
        print("   Le modèle peut nécessiter plus de données d'entraînement ou ajustement des hyperparamètres.")
    else:
        print("\n[OK] Modèle conforme (R² >= 0.70)")
    
    print("\n" + "=" * 60)
    print("[OK] Entraînement terminé avec succès")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    exit(main())
