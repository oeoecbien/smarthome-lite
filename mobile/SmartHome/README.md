# SmartHome App

Application Android de gestion domotique (Smart Home) développée avec Jetpack Compose.

## 🚀 Aperçu
Cette application permet de contrôler des appareils connectés (lampes, capteurs) via une interface moderne et intuitive. Elle inclut des fonctionnalités avancées comme la gestion de règles d'automatisation et des scénarios assistés par l'IA.

## 🏗️ Architecture
L'application suit le pattern **MVVM (Model-View-ViewModel)**. Pour une explication détaillée de chaque dossier et de chaque fonction, veuillez consulter le document dédié :

👉 **[Voir l'Architecture Détaillée (ARCHITECTURE.md)](./ARCHITECTURE.md)**

## 📂 Structure du projet (Résumé)
- `data/` : API, Modèles de données et Repository.
- `ui/` : Écrans Compose, ViewModels et Thème.
- `MainActivity.kt` : Point d'entrée et Navigation.

## 🛠️ Stack Technique
- **Langage** : Kotlin
- **UI** : Jetpack Compose
- **Réseau** : Retrofit / OkHttp
- **ViewModel** : Android Lifecycle ViewModels
- **Injection** : Repository Pattern manuel
- **Stockage** : Datastore (via TokenManager)
