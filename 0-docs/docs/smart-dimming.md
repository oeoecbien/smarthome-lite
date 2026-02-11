# Smart Dimming

Ajuste l’intensité des lampes (light/dimmer) selon la luminosité ambiante (lux) et le scénario IA. Déclenché à chaque nouvelle mesure `light_readings` (RPi envoie les lux).

**Config** : `app/config.py` → `dimming_params` par scénario (0=Day, 1=Night, 2=Away, 3=Evening). Seuils lux + intensités min/max. Scénario Away = smart dimming désactivé (fixed_brightness 0).

**Fichiers** : `app/services/smart_dimming_service.py`, `app/routes/smart_dimming.py`. Activation globale : `SMART_DIMMING_ENABLED` (config) ou endpoint `PUT /api/smart-dimming/enable`.

Endpoints : `GET /api/smart-dimming/status` (activé, adjustments_today, active_devices), `PUT /api/smart-dimming/enable` (body `{ "enabled": true }`), `POST /api/smart-dimming/simulate` (optionnel, body `{ "lux_value": 400 }` pour forcer un run).

`GET /health` n’expose pas le smart dimming ; voir `GET /api/smart-dimming/status`.
