# Structure de la Présentation Orale — SmartHome Lite

Guide pour construire les slides et le déroulé de la soutenance (SAE S5 — développement distribué et embarqué).

---

## 1. Ouverture (1–2 min)

- **Titre** : SmartHome Lite — Gestion intelligente de l’éclairage et des appareils
- **Cadre** : SAE BUT3 FA 2025, projet distribué et embarqué
- **Équipe** : prénoms et rôles (backend, mobile, RPi, IA / intégration)
- **Problématique** : domotique avec détection de présence, adaptation à la luminosité et automatisation pilotée par l’IA

**Message clé** : système en trois niveaux — contrôle manuel, automatisations par règles, adaptation contextuelle (IA + smart dimming).

---

## 2. Contexte et objectifs (2 min)

- **Contraintes** : 50 h, 4 personnes, Raspberry Pi, capteurs (présence Z-Wave, luminosité BH1750/LDR), actionneurs (lampes dimmables, prises)
- **Objectifs** :
  - Service distribué (backend déployé)
  - Au moins un Raspberry Pi dans l’architecture
  - Base de données hébergée (PostgreSQL + TimescaleDB)
  - Application mobile (Kotlin + Jetpack Compose)
  - Algorithme d’IA (classification de scénarios, prédiction d’intensité)
  - Contrôle à distance, détection de présence, smart dimming, automatisation par règles

**Slide suggéré** : liste à puces objectifs + contraintes.

---

## 3. Architecture globale (3 min)

- **Vue d’ensemble** : utiliser le diagramme `diagrams/architecture-globale.md` (Mermaid).
- **Couches** :
  1. **Clients** : application mobile (Kotlin/Compose), application web (Next.js) — HTTP/REST, JWT
  2. **Backend** : FastAPI, architecture modulaire (routes, services, modèles, schémas Pydantic), module ML (classification, régression)
  3. **Base de données** : PostgreSQL (tables relationnelles), TimescaleDB (séries temporelles, ex. `light_readings`)
  4. **Raspberry Pi** : API Flask locale, capteurs (présence, luminosité), actionneurs (LED/relais ou Z-Wave), communication Backend ↔ RPi via HTTP + API Key

- **Principes** : modularité, ORM (SQLAlchemy), validation (Pydantic), IA multi-modèles (classification, régression, clustering prévu).

**Slide suggéré** : une slide = schéma d’architecture (export PNG/SVG depuis [mermaid.live](https://mermaid.live/) ou extension VS Code).

---

## 4. Fonctionnalités principales (3–4 min)

### 4.1 Contrôle manuel (F1–F3)

- Lampes : ON/OFF, intensité 0–100 %
- Prises : ON/OFF
- Tableau de bord : état de tous les appareils, scénario actif, luminosité ambiante, statut smart dimming

### 4.2 Détection de présence (F4–F5)

- Capteur Z-Wave (ex. MultiSensor 7) → API Flask RPi → `POST /api/presence` → enregistrement + déclenchement des règles

### 4.3 Automatisation (F6–F7)

- Moteur de règles IF-THEN : conditions (présence, heure, jour, luminosité, état appareil), actions (allumer/éteindre, intensité, smart dimming)
- Scénarios : Jour, Soirée, Nuit, Absence (détectés par l’IA)

### 4.4 IA et Smart Dimming (F8–F9)

- **Classification** : Decision Tree → scénario actuel (Day, Night, Away, Evening)
- **Régression** : Random Forest → prédiction d’intensité optimale
- **Smart Dimming** : adaptation dynamique à la luminosité ambiante (mesure lux → calcul intensité cible → commande RPi), avec historique et pause par appareil

**Slide suggéré** : une slide par bloc (manuel / présence / règles / IA + smart dimming) ou un tableau récapitulatif.

---

## 5. Stack technique (1 min)

- **Backend** : Python 3.9+, FastAPI, Uvicorn, SQLAlchemy, Pydantic, JWT (python-jose), bcrypt, scikit-learn, joblib
- **Base de données** : PostgreSQL 14+, TimescaleDB (optionnel)
- **Mobile** : Kotlin, Jetpack Compose, Retrofit, DataStore
- **Web** : Next.js, React
- **Raspberry Pi** : Raspberry Pi OS, Flask, Z-Wave JS UI (si Z-Wave), GPIO / I²C (BH1750)

**Slide suggéré** : logos ou liste par couche.

---

## 6. Flux de données (2 min)

- **Contrôle manuel** : Mobile → Backend (JWT) → RPi (API Key) → lampe ; événement enregistré. Référence : `diagrams/flux-controle-manuel.md`.
- **Présence + règle** : Capteur → RPi → `POST /api/presence` → RuleEngine → action sur appareil. Référence : `diagrams/flux-presence-regle.md`.
- **Smart Dimming** : Capteur luminosité → `POST /api/light_readings` → SmartDimmingService + AIService → calcul intensité → commande RPi → enregistrement `dimming_adjustments`. Référence : `diagrams/flux-smart-dimming.md`.

**Slide suggéré** : une slide par flux avec schéma simplifié (ou export des diagrammes Mermaid en PNG/SVG).

---

## 7. Base de données (1 min)

- **Tables principales** : `users`, `raspberry_pis`, `devices`, `presence`, `light_readings`, `rules`, `events`, `dimming_adjustments`, `user_preferences`, `training_data`
- **Relations** : users → devices ; raspberry_pis → devices, presence, light_readings ; devices → events, dimming_adjustments
- **Schéma** : `diagrams/modele-donnees.md` (Mermaid)

**Slide suggéré** : schéma entité-relation (export du diagramme Mermaid en PNG/SVG).

---

## 8. Démonstration (5–6 min)

- **Connexion** : ouverture de l’app mobile, login (ex. admin / admin123)
- **Tableau de bord** : affichage des appareils, scénario, luminosité
- **Contrôle manuel** : allumage d’une lampe, réglage de l’intensité (slider), vérification sur la lampe réelle ou simulateur
- **Présence + règle** : déclencher le capteur de mouvement (ou simuler un POST), montrer l’exécution de la règle (ex. allumage automatique)
- **Smart Dimming** (si possible) : montrer une mesure de luminosité qui déclenche un ajustement, ou expliquer le flux avec les diagrammes

**Conseil** : préparer un scénario unique enchaîné (1–2–3) et le chronométrer.

---

## 9. Difficultés et solutions (2 min)

- **Exemples possibles** :
  - Synchronisation Backend ↔ RPi (timeout, API Key, gestion erreurs)
  - Qualité des données pour l’IA (génération synthétique, métriques)
  - UX mobile (optimistic UI, feedback immédiat)
  - Smart dimming : éviter les oscillations (hystérésis, pause utilisateur)

**Slide suggéré** : 2–3 lignes « Problème → Solution » par point.

---

## 10. Conclusion (1 min)

- **Bilan** : objectifs atteints (liste courte), livrables (code, doc, APK, vidéo)
- **Pistes d’évolution** : clustering (K-Means), WebSockets temps réel, apprentissage continu des préférences, intégration météo
- **Remerciements** : jury, encadrants

---

## 11. Questions possibles du jury

- **Architecture** : pourquoi FastAPI ? pourquoi monolithe modulaire plutôt que microservices ?
- **Sécurité** : JWT (durée, stockage), API Key RPi, validation des entrées
- **IA** : choix Decision Tree / Random Forest, métriques (accuracy, R²), réentraînement
- **Smart Dimming** : formules d’interpolation, seuils par scénario, protection contre les oscillations
- **Raspberry Pi** : protocole (HTTP vs MQTT), gestion des pannes réseau
- **Base de données** : rôle de TimescaleDB, volumétrie, rétention des données

---

## Durée indicative totale

| Partie              | Durée   |
|---------------------|---------|
| Ouverture           | 1–2 min |
| Contexte / objectifs| 2 min   |
| Architecture        | 3 min   |
| Fonctionnalités     | 3–4 min |
| Stack technique     | 1 min   |
| Flux de données     | 2 min   |
| Base de données     | 1 min   |
| Démo                | 5–6 min |
| Difficultés         | 2 min   |
| Conclusion          | 1 min   |
| **Total**           | **~20–22 min** |

Ajuster selon le temps imparti (ex. raccourcir stack + BDD si besoin).
