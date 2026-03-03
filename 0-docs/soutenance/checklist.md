# Checklist Soutenance — SmartHome Lite (SAE S5)

Checklist pour préparer et réussir la soutenance orale et les livrables associés.

---

## 1. Avant la soutenance

### Livrables techniques

- [ ] **Code source** : dépôt à jour, branches `main` / `develop` propres
- [ ] **Backend** : API FastAPI fonctionnelle, tests passants (`pytest`)
- [ ] **Application mobile** : APK signé (ou build debug) prêt à démontrer
- [ ] **Application web** (si livrée) : build Next.js OK
- [ ] **Raspberry Pi** : script/API Flask opérationnel, capteurs (présence, luminosité) et actionneurs (LED/relais ou Z-Wave) connectés
- [ ] **Base de données** : PostgreSQL (+ TimescaleDB si utilisé) avec schéma à jour et migrations appliquées
- [ ] **Modèles IA** : `scenario_classifier.pkl` et `regression_model.joblib` présents et chargés au démarrage

### Documentation

- [ ] **README principal** : à jour (architecture, installation, fonctionnalités)
- [ ] **README backend** : endpoints, configuration, ML
- [ ] **README Raspberry** : câblage, variables d’environnement, Z-Wave si utilisé
- [ ] **Documentation API** : Swagger/OpenAPI accessible (`/docs`) et cohérente avec le code
- [ ] **Guide utilisateur** (optionnel) : captures d’écran, tutoriel règles / smart dimming

### 1.3Diagrammes et schémas

- [ ] **Architecture globale** : clients (mobile, web) → Backend → DB + Raspberry Pi (voir `diagrams/architecture-globale.md`)
- [ ] **Modèle de données** : schéma entité-relation (tables principales et relations) (voir `diagrams/modele-donnees.md`)
- [ ] **Flux contrôle manuel** : allumage lampe (Mobile → Backend → RPi → lampe) (voir `diagrams/flux-controle-manuel.md`)
- [ ] **Flux détection de présence + règle** : capteur → RPi → Backend → RuleEngine → action (voir `diagrams/flux-presence-regle.md`)
- [ ] **Flux Smart Dimming** : luminosité → Backend → IA + SmartDimmingService → commande RPi (voir `diagrams/flux-smart-dimming.md`)
- [ ] **Pipeline IA** : classification → régression (→ clustering) → décision smart dimming (voir `diagrams/pipeline-ia.md`)

### Démo et environnement

- [ ] **Backend** : lancé et accessible (ex. `http://localhost:8000` ou URL de démo)
- [ ] **Base de données** : peuplée avec données de test (utilisateurs, appareils, règles, éventuellement présence/luminosité)
- [ ] **Raspberry Pi** : allumé, connecté au réseau, API Key configurée, au moins une lampe/prise contrôlable
- [ ] **Application mobile** : installée sur un appareil ou émulateur, compte de test (ex. admin/admin123) ou compte démo
- [ ] **Scénario de démo** : enchaînement répété (connexion → tableau de bord → allumage → règle présence → smart dimming si possible)

---

## 2. Présentation orale

### Support (slides)

- [ ] **Titre** : SmartHome Lite — SAE BUT3 FA 2025, noms de l’équipe
- [ ] **Contexte et objectifs** : cadre SAE, contraintes (50 h, 4 personnes, matériel)
- [ ] **Architecture** : schéma global (3 couches : clients / backend / RPi + DB)
- [ ] **Fonctionnalités** : contrôle manuel, détection présence, règles IF-THEN, IA (classification, régression), smart dimming
- [ ] **Stack technique** : FastAPI, Kotlin/Compose, PostgreSQL, Raspberry Pi, scikit-learn
- [ ] **Démo** : plan chronométré (contrôle manuel → présence + règle → smart dimming)
- [ ] **Difficultés et solutions** : 2–3 points (ex. sync RPi/backend, apprentissage IA, UX)
- [ ] **Conclusion** : bilan, pistes d’évolution

### Contenu à préparer

- [ ] **Répartition de parole** : qui présente quoi (intro, architecture, démo, IA, conclusion)
- [ ] **Réponses types** : durée du projet, répartition des rôles, choix techniques (FastAPI, JWT, TimescaleDB, etc.)
- [ ] **Points à valoriser** : modularité backend, moteur de règles, pipeline IA multi-modèles, smart dimming adaptatif

---

## Références

- **README projet** : `README.md` (racine) · **Backend** : `backend/README.md` · **Raspberry** : `raspberry/README.md`
- **Diagrammes** : `0-docs/soutenance/diagrams/*.md` · **Présentation** : `0-docs/soutenance/presentation.md`
- **Use case complexe** : `0-docs/soutenance/use-case-complexe.md`