# Analyse Critique de la Solution SAE - SmartHome Lite

## Contexte

Cette analyse remet en question la solution actuelle par rapport aux contraintes techniques définies dans le document `sae_but3fa_2025.pdf`.

---

## 1. Contraintes Techniques et État Actuel

### 1.1 Service Distribué Déployé sur Serveur

**Contrainte :** Le projet doit inclure un service distribué déployé sur un serveur.

**État actuel :** CONFORME
- Backend FastAPI bien structuré
- Architecture modulaire monolithique
- API REST complète avec documentation Swagger
- Déploiement possible via systemd

**Points positifs :**
- Architecture claire et maintenable
- Séparation des responsabilités (routes, services, models)
- Documentation API automatique

**Points d'amélioration :**
- Pas de mention explicite du déploiement sur un serveur dédié
- Configuration actuelle semble être en développement local
- Manque de documentation sur le déploiement en production

---

### 1.2 Intégration d'au moins un Raspberry Pi

**Contrainte :** Le projet doit intégrer au moins un Raspberry Pi dans son architecture.

**État actuel :** CONFORME
- Architecture prévue pour multiples Raspberry Pi
- Communication HTTP/REST entre backend et Raspberry Pi
- Gestion des capteurs (PIR, luminosité) et actionneurs
- API Flask locale sur chaque Raspberry Pi

**Points positifs :**
- Architecture prévue pour la scalabilité
- Gestion de plusieurs Raspberry Pi via l'API
- Heartbeat et gestion de l'état en ligne/hors ligne

**Points d'amélioration :**
- Le code source du Raspberry Pi n'est pas présent dans le repository (seulement README et config.example.py)
- Pas de preuve d'implémentation concrète du code Flask
- Manque de démonstration de l'intégration réelle

---

### 1.3 Base de Données Hébergée

**Contrainte :** Une base de données doit être hébergée sur l'une des machines du système.

**État actuel :** CONFORME
- PostgreSQL configuré sur `10.109.150.75:5432`
- Base de données `smarthome` créée
- Scripts d'initialisation présents
- Support TimescaleDB pour les time-series

**Points positifs :**
- Base de données centralisée et accessible
- Schéma bien défini avec relations
- Scripts de configuration automatisés

**Points d'amélioration :**
- La base de données est hébergée sur une machine distante (10.109.150.75), ce qui est conforme mais nécessite une connexion réseau stable
- Pas de mention si cette machine fait partie du système du projet ou est externe

---

### 1.4 Utilisation d'Actionneurs

**Contrainte :** L'utilisation d'actionneurs est encouragée mais non obligatoire.

**État actuel :** PARTIELLEMENT CONFORME
- Architecture prévue pour les actionneurs (LED, relais)
- Modèles de données pour les appareils (lampes, prises)
- Contrôle des états ON/OFF et brightness

**Points positifs :**
- Modèles de données complets
- API pour contrôler les appareils

**Points d'amélioration :**
- Pas de preuve d'implémentation matérielle réelle
- Le code Raspberry Pi manquant ne permet pas de vérifier l'intégration matérielle
- Pas de démonstration vidéo ou photos mentionnées

---

### 1.5 Application Mobile (CRITIQUE)

**Contrainte :** Le projet doit comprendre le développement d'une application mobile permettant :
- La visualisation des données issues du système
- L'interaction avec le serveur
- Réalisée en utilisant les technologies vues en cours : **Kotlin, Jetpack Compose et coroutines**

**État actuel :** NON CONFORME - CRITIQUE

**Problèmes identifiés :**
1. **Aucun code source présent** : Le dossier `mobile/` ne contient qu'un README.md
2. **Aucun fichier Kotlin** : Aucun fichier `.kt` trouvé dans le repository
3. **Aucun fichier Gradle** : Pas de `build.gradle`, `settings.gradle`, ou structure Android
4. **Documentation uniquement** : Le README décrit ce qui devrait être fait, mais rien n'est implémenté

**Impact :**
- **Contrainte obligatoire non respectée**
- Le projet ne peut pas être validé sans l'application mobile
- Manque critique dans les livrables

**Recommandations urgentes :**
1. Développer immédiatement l'application mobile Android
2. Utiliser Kotlin, Jetpack Compose et coroutines comme requis
3. Implémenter au minimum :
   - Authentification (login/register)
   - Visualisation des appareils
   - Contrôle des appareils (ON/OFF, brightness)
   - Visualisation des données (présence, luminosité)
   - Interaction avec le backend via API REST

---

### 1.6 Algorithme d'IA (Régression ou Classification)

**Contrainte :** Le projet devra intégrer au moins un algorithme d'IA permettant d'effectuer une régression ou une classification.

**État actuel :** PARTIELLEMENT CONFORME

**Ce qui est implémenté :**
- Classification : Decision Tree Classifier pour classification de scénarios (Day, Night, Away, Evening)
- Modèle entraîné et sauvegardé
- Service IA fonctionnel avec fallback
- Endpoints API pour la classification

**Ce qui manque :**
- Régression : Mentionnée dans la documentation mais non implémentée
  - F8.2 : Régression pour Prédiction d'Intensité (marqué "À implémenter")
  - Random Forest Regressor prévu mais non développé
- Clustering : Mentionné mais non implémenté
  - F8.3 : Clustering des Habitudes Utilisateur (marqué "À implémenter")

**Points positifs :**
- Classification fonctionnelle et intégrée
- Modèle entraîné avec données synthétiques
- Service bien structuré

**Points d'amélioration :**
- La contrainte demande "au moins un algorithme", donc la classification suffit
- Cependant, la documentation promet plus que ce qui est livré
- La régression serait un plus pour prédire l'intensité lumineuse optimale

**Recommandations :**
- La classification actuelle satisfait la contrainte minimale
- Pour aller au-delà, implémenter la régression pour améliorer le smart dimming

---

### 1.7 Accès au Serveur Ollama IUT

**Contrainte :** Un accès au serveur Ollama de l'IUT pourra être accordé pour les traitements d'intelligence artificielle.

**État actuel :** NON UTILISÉ

**Problèmes identifiés :**
- Ollama mentionné uniquement comme "si besoin IA avancée future"
- Aucune intégration avec Ollama
- Aucun code utilisant l'API Ollama
- Pas de configuration pour se connecter au serveur Ollama IUT

**Impact :**
- Cette contrainte est optionnelle ("pourra être accordé")
- Cependant, l'utilisation d'Ollama pourrait améliorer significativement le projet
- Ollama pourrait être utilisé pour :
  - Génération de descriptions intelligentes des scénarios
  - Analyse de texte pour les règles d'automatisation
  - Recommandations personnalisées basées sur l'historique

**Recommandations :**
- Intégrer Ollama pour enrichir l'expérience utilisateur
- Utiliser Ollama pour des fonctionnalités avancées d'IA générative

---

## 2. Synthèse des Problèmes Critiques

### Problèmes Bloquants (Doivent être résolus)

1. **Application Mobile Absente**
   - **Impact :** Contrainte obligatoire non respectée
   - **Priorité :** CRITIQUE
   - **Action :** Développer immédiatement l'application Android en Kotlin/Jetpack Compose

### Problèmes Importants (Recommandés)

2. **Code Raspberry Pi Manquant**
   - **Impact :** Impossible de vérifier l'intégration matérielle
   - **Priorité :** HAUTE
   - **Action :** Ajouter le code source Flask du Raspberry Pi

3. **Régression IA Non Implémentée**
   - **Impact :** Fonctionnalité promise mais non livrée
   - **Priorité :** MOYENNE
   - **Action :** Implémenter la régression pour prédiction d'intensité

4. **Ollama Non Utilisé**
   - **Impact :** Opportunité manquée d'enrichir le projet
   - **Priorité :** BASSE (optionnel)
   - **Action :** Intégrer Ollama pour fonctionnalités avancées

---

## 3. Points Forts de la Solution

1. **Architecture Backend Solide**
   - Structure modulaire claire
   - Séparation des responsabilités
   - Documentation API automatique

2. **Base de Données Bien Conçue**
   - Schéma relationnel complet
   - Support time-series avec TimescaleDB
   - Scripts d'initialisation automatisés

3. **Classification IA Fonctionnelle**
   - Modèle Decision Tree implémenté
   - Service IA intégré
   - Fallback en cas d'erreur

4. **Documentation Complète**
   - README détaillé
   - Documentation des endpoints
   - Guide de déploiement

---

## 4. Suggestions de Correctifs Détaillées

### 4.1 Application Mobile (Priorité CRITIQUE)

**Objectif :** Développer une application Android complète respectant les contraintes techniques du projet.

**Architecture recommandée :**
- Utiliser l'architecture MVVM (Model-View-ViewModel) pour séparer la logique métier de l'interface
- Implémenter une couche de repository pour gérer les appels API
- Utiliser Hilt ou Koin pour l'injection de dépendances
- Créer un module réseau avec Retrofit pour les appels HTTP
- Implémenter un système de gestion d'état avec StateFlow ou LiveData

**Structure de modules :**
- Module data : Contient les repositories, les modèles de données, et les services API
- Module domain : Contient les use cases et la logique métier
- Module ui : Contient les composables Jetpack Compose et les ViewModels
- Module di : Contient la configuration d'injection de dépendances

**Fonctionnalités minimales à implémenter :**

**Authentification :**
- Écran de connexion avec champs email et mot de passe
- Écran d'inscription avec validation des champs
- Stockage sécurisé du token JWT (SharedPreferences ou DataStore)
- Gestion automatique de l'expiration du token avec refresh si nécessaire
- Navigation automatique vers l'écran principal après authentification réussie

**Visualisation des appareils :**
- Écran principal listant tous les appareils avec leur état actuel
- Affichage des informations essentielles : nom, type, état (ON/OFF), localisation
- Indicateurs visuels pour différencier les types d'appareils (lampes, prises)
- Rafraîchissement périodique des données ou pull-to-refresh
- Filtrage par localisation ou type d'appareil

**Contrôle des appareils :**
- Interface pour activer/désactiver chaque appareil
- Contrôle de l'intensité lumineuse pour les lampes dimmables (slider)
- Feedback visuel immédiat lors des actions (optimistic UI)
- Gestion des erreurs avec messages d'erreur clairs
- Confirmation pour les actions critiques

**Visualisation des données :**
- Graphiques de présence dans le temps (utilisation d'une bibliothèque de graphiques)
- Graphiques de luminosité avec courbes temporelles
- Filtres par période (jour, semaine, mois)
- Export des données si nécessaire
- Statistiques résumées (moyennes, pics, tendances)

**Technologies à utiliser :**
- Kotlin comme langage principal
- Jetpack Compose pour tous les écrans d'interface
- Coroutines pour tous les appels asynchrones (API, base de données locale)
- Retrofit pour les appels HTTP REST
- Gson ou Moshi pour la sérialisation JSON
- Navigation Compose pour la navigation entre écrans
- Material Design 3 pour le design system

**Gestion des erreurs :**
- Intercepteurs réseau pour gérer les erreurs HTTP de manière centralisée
- Messages d'erreur utilisateur-friendly
- Retry automatique pour les erreurs réseau temporaires
- Mode hors ligne avec cache local si possible

**Tests :**
- Tests unitaires pour les ViewModels
- Tests d'intégration pour les repositories
- Tests UI avec Compose Testing pour les écrans critiques

**Déploiement :**
- Génération d'un APK de démonstration
- Configuration des permissions Android nécessaires
- Support des différentes tailles d'écran et orientations

---

### 4.2 Code Raspberry Pi (Priorité HAUTE)

**Objectif :** Implémenter le service Flask complet pour la communication avec le backend et le contrôle matériel.

**Architecture du service :**
- Service Flask principal avec endpoints REST locaux
- Modules séparés pour les capteurs (sensors) et actionneurs (actuators)
- Service de communication avec le backend (envoi d'événements, réception de commandes)
- Service de monitoring avec heartbeat périodique
- Gestion des erreurs et reconnexion automatique

**Gestion des capteurs :**
- Module pour le capteur PIR avec lecture périodique de l'état
- Module pour le capteur de luminosité (BH1750 ou LDR) avec calibration
- Threading pour les lectures de capteurs sans bloquer le service principal
- Détection de changements d'état avec seuils configurables
- Envoi automatique d'événements au backend lors de détections

**Gestion des actionneurs :**
- Module pour le contrôle des LED avec PWM pour le dimming
- Module pour le contrôle des relais pour les prises connectées
- Synchronisation de l'état avec le backend
- Exécution immédiate des commandes reçues du backend
- Vérification de l'état après chaque action

**Communication avec le backend :**
- Client HTTP avec requests ou httpx pour les appels API
- Authentification via API Key dans les headers
- Envoi périodique de heartbeat pour indiquer que le Raspberry Pi est en ligne
- Réception de commandes via polling ou webhooks si implémenté
- Gestion des timeouts et reconnexions
- Queue de messages pour les événements en cas de perte de connexion

**Configuration :**
- Fichier de configuration avec toutes les variables nécessaires
- Configuration des pins GPIO pour chaque capteur et actionneur
- Configuration de l'URL du backend et de l'API Key
- Paramètres de timing (intervalles de lecture, heartbeat)
- Logs structurés pour le débogage

**Sécurité :**
- Validation de l'API Key avant chaque communication
- Chiffrement des communications si HTTPS est disponible
- Protection contre les commandes malveillantes
- Limitation du taux de requêtes

**Démarrage automatique :**
- Service systemd pour démarrage au boot
- Gestion des erreurs au démarrage
- Logs dans un fichier dédié
- Scripts de monitoring de santé du service

**Documentation :**
- README détaillé avec instructions d'installation
- Schéma de connexion des composants matériels
- Exemples de configuration
- Guide de dépannage

---

### 4.3 Régression IA pour Prédiction d'Intensité (Priorité MOYENNE)

**Objectif :** Implémenter un modèle de régression pour prédire l'intensité lumineuse optimale selon le contexte.

**Collecte de données :**
- Créer une table ou étendre TrainingData pour stocker les données de régression
- Collecter les données historiques : luminosité ambiante, heure, jour, présence, préférences utilisateur
- Enregistrer les ajustements manuels de l'utilisateur comme données d'entraînement
- Générer des données synthétiques si nécessaire pour l'entraînement initial
- Valider la qualité des données (détection d'outliers, normalisation)

**Feature engineering :**
- Extraire les features pertinentes : heure, jour de la semaine, luminosité ambiante, scénario détecté, historique des préférences
- Normaliser les features numériques
- Encoder les features catégorielles (type de pièce, scénario)
- Créer des features dérivées (période de la journée, weekend vs semaine)

**Modèle de régression :**
- Utiliser Random Forest Regressor de scikit-learn comme prévu dans la documentation
- Configurer les hyperparamètres : nombre d'arbres, profondeur maximale, échantillons minimum
- Alternative : essayer d'autres algorithmes (Gradient Boosting, XGBoost) et comparer les performances
- Validation croisée pour évaluer la robustesse du modèle

**Entraînement :**
- Diviser les données en ensembles d'entraînement, validation et test
- Entraîner le modèle avec les données d'entraînement
- Évaluer avec les métriques de régression : R² score, MAE, RMSE
- Ajuster les hyperparamètres selon les résultats
- Sauvegarder le modèle entraîné au format joblib

**Intégration dans le service :**
- Créer un nouveau service de régression similaire au service de classification
- Charger le modèle au démarrage du backend
- Exposer un endpoint API pour obtenir la prédiction d'intensité
- Intégrer la prédiction dans le service de smart dimming
- Gérer les cas où le modèle n'est pas disponible (fallback sur règles fixes)

**Apprentissage continu :**
- Enregistrer les ajustements manuels de l'utilisateur comme nouvelles données d'entraînement
- Réentraîner périodiquement le modèle avec les nouvelles données
- Comparer les performances avant et après réentraînement
- Versionner les modèles pour pouvoir revenir en arrière si nécessaire

**Évaluation et monitoring :**
- Suivre les métriques de performance en production
- Comparer les prédictions avec les ajustements réels de l'utilisateur
- Identifier les cas où le modèle performe mal
- Ajuster le modèle selon les retours

---

### 4.4 Intégration Ollama (Priorité BASSE - Optionnel)

**Objectif :** Intégrer le serveur Ollama de l'IUT pour enrichir l'expérience utilisateur avec des fonctionnalités d'IA générative.

**Configuration de la connexion :**
- Obtenir l'URL et les credentials du serveur Ollama IUT
- Configurer les paramètres de connexion dans le fichier de configuration
- Implémenter un client HTTP pour communiquer avec l'API Ollama
- Gérer l'authentification si nécessaire
- Tester la connectivité au serveur

**Fonctionnalités possibles :**

**Génération de descriptions intelligentes :**
- Utiliser Ollama pour générer des descriptions automatiques des scénarios détectés
- Créer des résumés intelligents de l'activité du système
- Générer des recommandations personnalisées basées sur les habitudes

**Analyse de texte pour les règles :**
- Permettre à l'utilisateur de créer des règles en langage naturel
- Utiliser Ollama pour parser et convertir le texte en règles structurées
- Valider la syntaxe et la logique des règles générées

**Recommandations personnalisées :**
- Analyser l'historique d'utilisation avec Ollama
- Générer des suggestions d'optimisation énergétique
- Proposer des scénarios d'automatisation adaptés aux habitudes

**Implémentation :**
- Créer un service Ollama dans le backend
- Exposer des endpoints API pour les fonctionnalités utilisant Ollama
- Gérer les erreurs et timeouts (Ollama peut être lent)
- Mettre en cache les réponses fréquentes pour améliorer les performances
- Intégrer dans l'application mobile si pertinent

**Documentation :**
- Documenter les modèles Ollama utilisés
- Expliquer les cas d'usage de chaque fonctionnalité
- Fournir des exemples de prompts efficaces

---

### 4.5 Améliorations Complémentaires

**Documentation de déploiement :**
- Créer un guide de déploiement en production détaillé
- Documenter la configuration du serveur (système d'exploitation, dépendances)
- Expliquer la configuration de la base de données en production
- Fournir des scripts de déploiement automatisés si possible
- Documenter les procédures de backup et de restauration

**Tests et validation :**
- Ajouter des tests unitaires pour les services critiques
- Implémenter des tests d'intégration pour les communications entre composants
- Tester les scénarios d'erreur (perte de connexion, données invalides)
- Valider les performances sous charge
- Tester la compatibilité avec différents appareils Android

**Sécurité renforcée :**
- Implémenter HTTPS pour toutes les communications
- Valider et sanitizer toutes les entrées utilisateur
- Ajouter des rate limiting sur les endpoints sensibles
- Implémenter une rotation des tokens JWT
- Auditer les logs pour détecter les tentatives d'intrusion

**Monitoring et observabilité :**
- Ajouter des logs structurés pour faciliter le débogage
- Implémenter des métriques de performance (temps de réponse, taux d'erreur)
- Créer un dashboard de monitoring si possible
- Configurer des alertes pour les erreurs critiques
- Documenter les procédures de maintenance

---

## 5. Conclusion

La solution actuelle présente une **architecture backend solide** et une **classification IA fonctionnelle**, mais souffre d'un **manque critique** : **l'application mobile est absente**.

**Pour valider le projet :**
1. Service distribué : CONFORME
2. Raspberry Pi : Architecture prévue (code à vérifier)
3. Base de données : CONFORME
4. Actionneurs : Architecture prévue (matériel à vérifier)
5. Application mobile : NON CONFORME - À DÉVELOPPER URGAMMENT
6. Algorithme d'IA : CONFORME (classification implémentée)

**Recommandation finale :** 

Le projet nécessite un effort de développement immédiat et ciblé pour répondre aux contraintes obligatoires. La priorité absolue doit être accordée au développement de l'application mobile Android, car c'est une contrainte non négociable du cahier des charges. Les suggestions de correctifs détaillées dans la section 4 fournissent un plan d'action structuré pour chaque problème identifié.

L'architecture backend existante constitue une base solide qui facilitera l'intégration des composants manquants. Une fois l'application mobile développée et le code Raspberry Pi implémenté, le projet sera conforme aux exigences minimales. Les améliorations supplémentaires (régression IA, Ollama) permettront de dépasser les attentes et de démontrer une maîtrise approfondie des technologies.