# Règles d’automatisation

IF condition THEN action. Table `rules`. Condition : JSON (AND/OR, time, presence, light, scenario). Action : `turn_on` / `turn_off` / `set_brightness` + `device_id`.

**Déclencheurs** : présence enregistrée (`POST /api/presence`), changement état/intensité manuel (pas si source=automatic). Test manuel : `POST /api/rules/{id}/test` (exécute toutes les règles, retourne si cette règle a tiré).

**Fichiers** : `app/routes/rules.py`, `app/services/rule_engine.py`, `app/utils/validators.py` (validate_rule_condition, validate_rule_action).

Tester une règle (JWT requis) :

```bash
curl -X POST "http://localhost:8000/api/rules/1/test" -H "Authorization: Bearer <JWT>"
```

Page : `/rules`. Bouton « Tester » sur la carte = appel à l’API test ; l’action est vraiment exécutée.
