# Architecture de l'application SmartHome

Ce document décrit l'architecture technique de l'application mobile SmartHome, basée sur le pattern **MVVM (Model-View-ViewModel)** recommandé par Google pour Android avec **Jetpack Compose**.

## Structure Globale

L'application est structurée en deux grandes couches principales situées dans `app/src/main/java/com/example/smarthome/` :
1.  **`data/`** : Gestion des données, appels API et logique métier.
2.  **`ui/`** : Interface utilisateur, états de l'écran et thèmes.

---

## 1. Couche Data (`data/`)

Cette couche est responsable de la récupération et de la manipulation des données (via API ou caches).

### `api/` (Communication Réseau)
-   **`SmartHomeApi.kt`** : Interface Retrofit définissant tous les points d'entrée de l'API (Login, Register, Devices, Rules, AI, etc.).
-   **`RetrofitInstance.kt`** : Singleton configurant Retrofit et le client HTTP.
-   **`TokenManager.kt`** : Gère le stockage sécurisé du token JWT de l'utilisateur.

### `model/` (Modèles de données)
Contient les classes de données (POJO/DTO) utilisées pour mapper les réponses JSON de l'API et représenter les objets dans l'app.
-   **`SmartDevice.kt`**, **`ApiDevice.kt`** : Représentation des appareils connectés.
-   **`Rule.kt`** : Modèles pour les règles d'automatisation.
-   **`AIScenario.kt`** : Modèles pour les scénarios générés par l'IA.
-   **`LoginRequest.kt`**, **`RegisterRequest.kt`**, **`TokenResponse.kt`** : Modèles pour l'authentification.

### `repository/` (Abstractions de données)
Le repository sert de source de vérité unique pour le ViewModel.
-   **`SmartHomeRepository.kt`** : Interface définissant les méthodes de récupération de données.
-   **`RealSmartHomeRepository.kt`** : Implémentation concrète appelant l'API via Retrofit.
-   **`FakeSmartHomeRepository.kt`** : Implémentation de test avec des données statiques.
-   **`RepositoryProvider.kt`** : Gère l'injection du repository (choix entre Real ou Fake).

---

## 2. Couche UI (`ui/`)

Cette couche gère l'affichage et l'interaction utilisateur via **Jetpack Compose**.

### `viewmodel/` (Logique de l'UI)
-   **`SmartHomeViewModel.kt`** : Le cerveau de l'UI. Il gère l'état de l'application (liste des devices, erreurs, chargement), appelle le repository et survit aux changements de configuration. Il contient toute la logique de login, refresh auto, et modifications d'appareils.

### `screens/` (Écrans complets)
Chaque fichier représente un écran majeur de l'application.
-   **`HomeScreen.kt`** : Tableau de bord principal listant les appareils.
-   **`LoginScreen.kt`** / **`RegisterScreen.kt`** / **`ResetPasswordScreen.kt`** : Gestion du cycle d'authentification.
-   **`LampControlScreen.kt`** : Contrôle détaillé d'une lampe (luminosité, état).
-   **`RulesScreen.kt`** / **`RuleDetailsScreen.kt`** : Gestion des règles d'automatisation.
-   **`SmartDimmingScreen.kt`** : Configuration du "Dimming" intelligent.
-   **`AIScreen.kt`** : Interface pour les scénarios d'IA.
-   **`ProfileScreen.kt`** : Infos utilisateur et déconnexion.
-   **`EventsScreen.kt`** : Historique des événements.

### `components/` (Composants réutilisables)
Contient des éléments d'UI partagés entre plusieurs écrans (boutons personnalisés, cartes, etc.).

### `theme/` (Design System)
-   **`Color.kt`**, **`Theme.kt`**, **`Type.kt`** : Définition des couleurs, polices et du thème global (Dark/Light mode).

---

## 3. Navigation et Point d'Entrée

-   **`MainActivity.kt`** : Point d'entrée de l'application. Il contient la logique de navigation principale et le conteneur (`Scaffold`) qui affiche la barre de navigation et les écrans selon la destination choisie.

---

## Flux de Données (Exemple : Toggle d'une lampe)
1.  **UI** : L'utilisateur clique sur un interrupteur dans `HomeScreen.kt`.
2.  **ViewModel** : `SmartHomeViewModel.updateDevice()` est appelé.
3.  **Repository** : Le ViewModel demande au `SmartHomeRepository` de mettre à jour l'état.
4.  **API** : Le repository fait un appel `PUT` via `SmartHomeApi`.
5.  **UI** : L'état est mis à jour dans le ViewModel (Compose), ce qui déclenche une recomposition de l'écran.
