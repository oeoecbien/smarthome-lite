# Guide de Déploiement en Production

Ce guide décrit les étapes pour déployer SmartHome Lite en production sur un serveur.

## Prérequis

### Serveur

- **Système d'exploitation** : Linux (Ubuntu 20.04+ ou Debian 11+ recommandé)
- **RAM** : Minimum 2 Go (4 Go recommandé)
- **CPU** : 2 cœurs minimum
- **Espace disque** : 10 Go minimum
- **Accès** : SSH avec droits sudo

### Logiciels requis

- Python 3.9+
- PostgreSQL 14+
- Git
- Nginx (optionnel, pour reverse proxy)

## Installation

### 1. Préparation du serveur

```bash
# Mettre à jour le système
sudo apt update && sudo apt upgrade -y

# Installer les dépendances système
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib git nginx
```

### 2. Configuration PostgreSQL

```bash
# Se connecter à PostgreSQL
sudo -u postgres psql

# Créer la base de données
CREATE DATABASE smarthome;

# Créer un utilisateur (remplacer 'password' par un mot de passe sécurisé)
CREATE USER smarthome_user WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE smarthome TO smarthome_user;

# Activer TimescaleDB (optionnel, pour time-series)
\c smarthome
CREATE EXTENSION IF NOT EXISTS timescaledb;

# Quitter
\q
```

### 3. Clonage du repository

```bash
# Créer un répertoire pour l'application
sudo mkdir -p /opt/smarthome
sudo chown $USER:$USER /opt/smarthome

# Cloner le repository
cd /opt/smarthome
git clone <repo-url> .

# Ou copier les fichiers manuellement
```

### 4. Configuration de l'environnement

```bash
cd /opt/smarthome/backend

# Créer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configuration des variables d'environnement

Créer un fichier `.env` dans `/opt/smarthome/backend/` :

```bash
# Base de données
DATABASE_URL=postgresql://smarthome_user:password@localhost:5432/smarthome
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=smarthome
DATABASE_USER=smarthome_user
DATABASE_PASSWORD=password

# JWT
SECRET_KEY=votre_secret_key_aleatoire_32_caracteres_minimum
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Serveur
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False
ENVIRONMENT=production

# CORS (ajuster selon vos besoins)
CORS_ORIGINS=["https://votre-domaine.com"]

# Ollama (optionnel)
OLLAMA_BASE_URL=http://ollama.iut.local:11434
OLLAMA_MODEL=llama2
OLLAMA_TIMEOUT=30
```

**Important** : Générer une clé secrète sécurisée :

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 6. Initialisation de la base de données

```bash
cd /opt/smarthome/backend
source venv/bin/activate

# Exécuter le script d'initialisation
psql -U smarthome_user -d smarthome -f ../db/init_database.sql

# Ou via Python
python -c "from app.database import init_db; init_db()"
```

### 7. Génération et entraînement des modèles IA

```bash
cd /opt/smarthome/backend

# Générer les données d'entraînement pour la classification
python ml/generate_data.py --samples 500

# Entraîner le modèle de classification
python ml/train_model.py --max-depth 7

# Générer les données pour la régression
python ml/generate_regression_data.py --samples 800

# Entraîner le modèle de régression
python ml/train_regression_model.py --n-estimators 100 --max-depth 10
```

### 8. Configuration systemd

Créer un fichier `/etc/systemd/system/smarthome.service` :

```ini
[Unit]
Description=SmartHome Lite API
After=network.target postgresql.service

[Service]
Type=simple
User=smarthome
WorkingDirectory=/opt/smarthome/backend
Environment="PATH=/opt/smarthome/backend/venv/bin"
ExecStart=/opt/smarthome/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Activer et démarrer le service :

```bash
# Créer un utilisateur dédié (optionnel mais recommandé)
sudo useradd -r -s /bin/false smarthome
sudo chown -R smarthome:smarthome /opt/smarthome

# Recharger systemd
sudo systemctl daemon-reload

# Activer le service
sudo systemctl enable smarthome

# Démarrer le service
sudo systemctl start smarthome

# Vérifier le statut
sudo systemctl status smarthome
```

### 9. Configuration Nginx (optionnel, pour HTTPS)

Créer un fichier `/etc/nginx/sites-available/smarthome` :

```nginx
server {
    listen 80;
    server_name votre-domaine.com;

    # Redirection HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name votre-domaine.com;

    ssl_certificate /etc/letsencrypt/live/votre-domaine.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/votre-domaine.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Activer la configuration :

```bash
sudo ln -s /etc/nginx/sites-available/smarthome /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Configuration du Firewall

```bash
# Autoriser SSH
sudo ufw allow 22/tcp

# Autoriser HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Autoriser le port de l'API (si accès direct nécessaire)
sudo ufw allow 8000/tcp

# Activer le firewall
sudo ufw enable
```

## Procédures de Backup

### Backup de la base de données

Créer un script `/opt/smarthome/scripts/backup.sh` :

```bash
#!/bin/bash
BACKUP_DIR="/opt/smarthome/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/smarthome_$DATE.sql"

mkdir -p $BACKUP_DIR

# Backup PostgreSQL
pg_dump -U smarthome_user -d smarthome > $BACKUP_FILE

# Compresser
gzip $BACKUP_FILE

# Garder seulement les 7 derniers backups
find $BACKUP_DIR -name "smarthome_*.sql.gz" -mtime +7 -delete

echo "Backup créé: $BACKUP_FILE.gz"
```

Rendre le script exécutable :

```bash
chmod +x /opt/smarthome/scripts/backup.sh
```

Ajouter une tâche cron pour backup quotidien :

```bash
# Éditer le crontab
crontab -e

# Ajouter cette ligne (backup à 2h du matin)
0 2 * * * /opt/smarthome/scripts/backup.sh
```

### Backup des modèles IA

```bash
#!/bin/bash
BACKUP_DIR="/opt/smarthome/backups/models"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Copier les modèles
cp -r /opt/smarthome/backend/ml/models $BACKUP_DIR/models_$DATE

# Compresser
tar -czf $BACKUP_DIR/models_$DATE.tar.gz -C $BACKUP_DIR models_$DATE
rm -rf $BACKUP_DIR/models_$DATE

echo "Backup modèles créé: $BACKUP_DIR/models_$DATE.tar.gz"
```

## Procédures de Restauration

### Restauration de la base de données

```bash
# Restaurer depuis un backup
gunzip < /opt/smarthome/backups/smarthome_20250115_020000.sql.gz | psql -U smarthome_user -d smarthome
```

### Restauration des modèles IA

```bash
# Extraire et copier les modèles
tar -xzf /opt/smarthome/backups/models/models_20250115.tar.gz
cp -r models_20250115/* /opt/smarthome/backend/ml/models/
```

## Monitoring et Maintenance

### Logs

Les logs sont disponibles via journald :

```bash
# Voir les logs du service
sudo journalctl -u smarthome -f

# Voir les logs des dernières 100 lignes
sudo journalctl -u smarthome -n 100
```

### Vérification de santé

```bash
# Vérifier que l'API répond
curl http://localhost:8000/health

# Vérifier la base de données
psql -U smarthome_user -d smarthome -c "SELECT COUNT(*) FROM devices;"
```

### Mise à jour

```bash
# Arrêter le service
sudo systemctl stop smarthome

# Faire un backup
/opt/smarthome/scripts/backup.sh

# Mettre à jour le code
cd /opt/smarthome
git pull

# Mettre à jour les dépendances
cd backend
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Redémarrer le service
sudo systemctl start smarthome
```

## Dépannage

### Le service ne démarre pas

```bash
# Vérifier les logs
sudo journalctl -u smarthome -n 50

# Vérifier la configuration
sudo systemctl status smarthome

# Tester manuellement
cd /opt/smarthome/backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Problèmes de base de données

```bash
# Vérifier que PostgreSQL est démarré
sudo systemctl status postgresql

# Vérifier la connexion
psql -U smarthome_user -d smarthome -c "SELECT 1;"
```

### Problèmes de permissions

```bash
# Vérifier les permissions
ls -la /opt/smarthome

# Corriger les permissions
sudo chown -R smarthome:smarthome /opt/smarthome
```

## Sécurité

### Recommandations

1. **Changer les mots de passe par défaut**
2. **Utiliser HTTPS en production**
3. **Configurer un firewall**
4. **Mettre à jour régulièrement le système**
5. **Limiter l'accès SSH (clés au lieu de mots de passe)**
6. **Configurer des backups automatiques**
7. **Monitorer les logs pour détecter les intrusions**

### Rate Limiting

Pour limiter le nombre de requêtes, configurer Nginx :

```nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

server {
    location /api/ {
        limit_req zone=api_limit burst=20;
        proxy_pass http://127.0.0.1:8000;
    }
}
```

## Support

Pour toute question ou problème, consulter :
- La documentation dans `docs/`
- Les logs du service
- Le README principal
