# Application Mobile Android

Application Android développée en Kotlin avec Jetpack Compose. Elle est le **client mobile** du projet SmartHome Lite ; le **client web** (Next.js) utilise le même backend.

## Fonctionnalités

- Contrôle des appareils en temps réel
- Synchronisation via WebSockets
- Visualisation des données
- Configuration des règles
- Monitoring du smart dimming

## Technologies

- Kotlin 1.9+
- Jetpack Compose
- Retrofit (REST API)
- WebSocket client
- Hilt (Dependency Injection)
- StateFlow & Coroutines

## Installation

1. Ouvrir le projet avec Android Studio (`mobile/SmartHome/`)
2. Synchroniser Gradle
3. Configurer l'URL du backend dans `app/src/main/res/values/config.xml`
4. Build & Run

## Configuration

Éditer `SmartHome/app/src/main/res/values/config.xml` :

```xml
<string name="backend_url">http://votre-serveur:8000</string>
<string name="websocket_url">ws://votre-serveur:8000/ws</string>
```

## Build APK

Depuis `mobile/SmartHome/` :

```bash
./gradlew assembleRelease
```

L'APK sera généré dans `app/build/outputs/apk/release/`

## Structure

```
mobile/SmartHome/app/src/main/java/com/example/smarthome/
├── data/          # Couche données (Repository, API)
├── ui/            # Interface utilisateur (Compose)
├── viewmodel/     # ViewModels (MVVM)
└── di/            # Injection de dépendances (Hilt)
```

