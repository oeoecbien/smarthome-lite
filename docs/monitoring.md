# Guide de Monitoring et Observabilité

Ce guide décrit comment monitorer et observer le système SmartHome Lite en production.

## Endpoints de Monitoring

### Health Check

**Endpoint** : `GET /health`

Vérifie l'état de santé de l'API et de ses dépendances.

**Réponse** :
```json
{
  "status": "healthy",
  "database": "connected",
  "ai_service": "loaded",
  "regression_service": "loaded",
  "ollama": "enabled",
  "environment": "production"
}
```

**Codes de statut** :
- `200` : Système sain
- `503` : Problème détecté (base de données, services, etc.)

### Métriques de Performance

**Endpoint** : `GET /metrics`

Retourne les métriques de performance de l'API.

**Réponse** :
```json
{
  "total_requests": 1250,
  "total_errors": 12,
  "error_rate": 0.96,
  "avg_response_time": 0.045,
  "endpoints": {
    "GET /api/devices": {
      "count": 450,
      "errors": 2,
      "avg_time": 0.032
    },
    "POST /api/auth/login": {
      "count": 120,
      "errors": 5,
      "avg_time": 0.089
    }
  },
  "timestamp": "2025-01-15T14:30:00"
}
```

## Logs

### Format des Logs

Les logs sont structurés avec le format suivant :

```
2025-01-15 14:30:00 - app.main - INFO - GET /api/devices [200] (0.032s) - 192.168.1.100
```

**Composants** :
- Timestamp
- Module
- Niveau (DEBUG, INFO, WARNING, ERROR)
- Méthode HTTP et endpoint
- Code de statut
- Temps de traitement
- IP du client

### Niveaux de Log

- **DEBUG** : Informations détaillées pour le débogage
- **INFO** : Événements normaux (requêtes, opérations réussies)
- **WARNING** : Situations anormales mais non critiques
- **ERROR** : Erreurs nécessitant une attention

### Consultation des Logs

#### Via journald (systemd)

```bash
# Voir les logs en temps réel
sudo journalctl -u smarthome -f

# Voir les 100 dernières lignes
sudo journalctl -u smarthome -n 100

# Filtrer par niveau
sudo journalctl -u smarthome -p err

# Filtrer par période
sudo journalctl -u smarthome --since "2025-01-15 14:00:00"
```

#### Via fichiers (si configuré)

```bash
# Voir les logs
tail -f /var/log/smarthome/app.log

# Rechercher des erreurs
grep ERROR /var/log/smarthome/app.log
```

## Métriques à Surveiller

### Métriques Critiques

1. **Taux d'erreur** : Doit rester < 1%
2. **Temps de réponse moyen** : Doit rester < 200ms
3. **Disponibilité de la base de données** : Doit être "connected"
4. **État des services IA** : Modèles chargés ou fallback actif

### Métriques de Performance

1. **Requêtes par minute** : Surveiller les pics
2. **Temps de réponse par endpoint** : Identifier les endpoints lents
3. **Taux d'erreur par endpoint** : Identifier les problèmes spécifiques

### Métriques Métier

1. **Nombre d'appareils actifs**
2. **Nombre de détections de présence**
3. **Nombre d'ajustements smart dimming**
4. **Utilisation des modèles IA**

## Alertes Recommandées

### Alertes Critiques

- **Base de données inaccessible** : Erreur immédiate
- **Taux d'erreur > 5%** : Attention requise
- **Temps de réponse > 1s** : Performance dégradée
- **Service IA non disponible** : Fallback actif

### Alertes d'Avertissement

- **Taux d'erreur > 1%** : Surveiller
- **Temps de réponse > 500ms** : Performance à surveiller
- **Disque plein (> 80%)** : Nettoyage nécessaire

## Dashboard de Monitoring (Optionnel)

### Prometheus + Grafana

Pour un monitoring avancé, configurer Prometheus et Grafana :

1. **Exporter les métriques** : Créer un endpoint `/metrics` au format Prometheus
2. **Configurer Prometheus** : Scraper les métriques toutes les 15 secondes
3. **Créer des dashboards Grafana** : Visualiser les métriques

### Exemple de Configuration Prometheus

```yaml
scrape_configs:
  - job_name: 'smarthome'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:8000']
```

## Maintenance

### Tâches Régulières

1. **Vérification quotidienne** : Consulter `/health` et `/metrics`
2. **Analyse des logs** : Rechercher les erreurs et warnings
3. **Nettoyage des backups** : Supprimer les backups anciens
4. **Mise à jour des dépendances** : Mettre à jour régulièrement

### Procédures de Dépannage

#### API lente

1. Vérifier les métriques : `GET /metrics`
2. Identifier les endpoints lents
3. Vérifier la charge de la base de données
4. Vérifier les ressources système (CPU, RAM)

#### Erreurs fréquentes

1. Consulter les logs : `journalctl -u smarthome -p err`
2. Identifier le pattern d'erreurs
3. Vérifier la configuration
4. Vérifier la connectivité avec les dépendances

#### Base de données inaccessible

1. Vérifier que PostgreSQL est démarré : `sudo systemctl status postgresql`
2. Vérifier la connexion : `psql -U smarthome_user -d smarthome`
3. Vérifier les logs PostgreSQL : `sudo journalctl -u postgresql`

## Intégration avec des Outils Externes

### Sentry (Gestion d'erreurs)

Pour un suivi avancé des erreurs, intégrer Sentry :

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="votre-dsn-sentry",
    integrations=[FastApiIntegration()],
    traces_sample_rate=1.0
)
```

### Datadog / New Relic

Pour un monitoring complet, intégrer un APM (Application Performance Monitoring) :

- Configuration des agents
- Instrumentation automatique
- Dashboards personnalisés

## Bonnes Pratiques

1. **Logs structurés** : Utiliser un format JSON pour faciliter l'analyse
2. **Correlation IDs** : Ajouter un ID unique à chaque requête pour le traçage
3. **Alertes intelligentes** : Éviter les alertes trop fréquentes
4. **Rétention des logs** : Conserver les logs au moins 30 jours
5. **Backup des métriques** : Sauvegarder les métriques historiques
