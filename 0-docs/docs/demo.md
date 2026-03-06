# Enchaînement type pour la démo

- **Connexion** : l’application mobile ou web envoie `POST /api/auth/login` et reçoit un JWT ; les requêtes suivantes incluent `Authorization: Bearer <token>`.
- **Contrôle manuel** : un `PUT` sur `/api/devices/<id>/state` ou `/brightness` est traité par le backend (après vérification du JWT), puis `DeviceService` envoie un POST à l’URL du RPi (`/api/devices/<gpio_pin>/state` ou `/brightness`) avec le header `X-API-Key` ; l’API Flask du RPi appelle le client Z-Wave, qui pilote la lampe ; le backend met à jour la base et enregistre l’événement.
- **Présence et règle** : le capteur Z-Wave détecte un mouvement ; le RPi envoie `POST /api/presence` (ou le backend lit le capteur) ; le backend enregistre la présence en base et appelle `RuleEngine.evaluate_rules` avec le déclencheur `presence_detected` ; les actions (allumage ou réglage de lampes) sont exécutées via `DeviceService`.
- **Smart dimming** : une mesure de luminosité est enregistrée dans `light_readings` ; `SmartDimmingService.process_light_reading` est appelé ; le scénario IA et l’intensité cible sont calculés ; les commandes sont envoyées au RPi et les ajustements sont enregistrés.
