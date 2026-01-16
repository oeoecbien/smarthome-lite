# Guide d'Initialisation Base de Données SmartHome Lite

## Table des Matières

1. [Prérequis](#prérequis)
2. [Installation PostgreSQL](#installation-postgresql)
3. [Initialisation de la Base](#initialisation-de-la-base)
4. [Vérification](#vérification)
5. [Configuration Backend](#configuration-backend)
6. [Commandes Utiles](#commandes-utiles)
7. [Dépannage](#dépannage)
8. [Schéma de Données](#schéma-de-données)

---

## Prérequis

### Versions Requises
- **PostgreSQL** : 14.0 ou supérieur
- **TimescaleDB** : Extension optionnelle pour optimiser les time-series (recommandé)
- **Système** : Linux (Ubuntu/Debian recommandé), macOS, ou Windows
- **Droits** : Accès administrateur (sudo) pour créer la base

### Ports par Défaut
- PostgreSQL : `5432`
- Backend FastAPI : `8000`

---

## Installation PostgreSQL

### Sur Ubuntu/Debian

```bash
# Mise à jour des paquets
sudo apt update

# Installation PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Installation TimescaleDB (optionnel mais recommandé)
sudo apt install timescaledb-2-postgresql-14 -y

# Configuration TimescaleDB
sudo timescaledb-tune

# Démarrage du service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Vérification du statut
sudo systemctl status postgresql
```

### Sur macOS (avec Homebrew)

```bash
# Installation PostgreSQL
brew install postgresql@14

# Installation TimescaleDB (optionnel)
brew tap timescale/tap
brew install timescaledb

# Démarrage du service
brew services start postgresql@14

# Vérification
psql --version
```

### Sur Raspberry Pi OS

```bash
# Installation
sudo apt update
sudo apt install postgresql postgresql-contrib -y

# Configuration pour accepter les connexions locales
sudo nano /etc/postgresql/14/main/pg_hba.conf
# Vérifier la ligne: local all postgres peer

# Redémarrage
sudo systemctl restart postgresql
```

---

## Initialisation de la Base

### Étape 1 : Connexion à PostgreSQL

```bash
# Se connecter en tant qu'utilisateur postgres
sudo -u postgres psql
```

Vous devriez voir le prompt `postgres=#`

### Étape 2 : Exécuter le Script d'Initialisation

**Option A : Depuis psql (recommandé)**

```bash
# Se placer dans le répertoire contenant init_database.sql
cd /chemin/vers/sae_s5/db

# Exécuter le script
sudo -u postgres psql -f init_database.sql
```

**Option B : Depuis psql interactif**

```sql
-- Dans le prompt psql
\c smarthome
\i /chemin/vers/db/init_database.sql
```

**Note :** Le script crée automatiquement la base de données `smarthome` si elle n'existe pas.

### Étape 3 : Activer TimescaleDB (Optionnel)

Si TimescaleDB est installé, convertir la table `light_readings` en hypertable pour optimiser les requêtes time-series :

```sql
-- Se connecter à la base
sudo -u postgres psql -d smarthome

-- Activer l'extension TimescaleDB
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Convertir la table en hypertable
SELECT create_hypertable('light_readings', 'measured_at');

-- Vérifier la création
SELECT * FROM timescaledb_information.hypertables;
```

### Étape 4 : Vérifier la Création

```bash
# Lister les bases de données
sudo -u postgres psql -c "\l"

# Vous devriez voir 'smarthome' dans la liste

# Se connecter à la base
sudo -u postgres psql -d smarthome

# Lister les tables
\dt
```

**Tables attendues :**
- `users`
- `raspberry_pis`
- `devices`
- `presence`
- `bluetooth_devices`
- `light_readings`
- `events`
- `rules`
- `training_data`
- `smart_dimming_adjustments`
- `user_preferences`

---

## Vérification

### Vérifier les Données de Test

```sql
-- Se connecter à la base
sudo -u postgres psql -d smarthome

-- Vérifier les utilisateurs
SELECT id, username, email FROM users;

-- Vérifier les Raspberry Pi
SELECT id, name, location, is_online FROM raspberry_pis;

-- Vérifier les appareils
SELECT d.name, d.type, r.location 
FROM devices d 
JOIN raspberry_pis r ON d.raspberry_pi_id = r.id;

-- Vérifier les règles
SELECT id, name, enabled FROM rules;

-- Vérifier les données IA
SELECT scenario, COUNT(*) 
FROM training_data 
GROUP BY scenario;

-- Vérifier les ajustements Smart Dimming
SELECT COUNT(*) FROM smart_dimming_adjustments;

-- Vérifier les préférences utilisateur
SELECT COUNT(*) FROM user_preferences;

-- Vérifier les mesures de luminosité
SELECT COUNT(*) FROM light_readings;

-- Vérifier les devices Bluetooth associés
SELECT COUNT(*) FROM bluetooth_devices;

-- Vérifier les détections Bluetooth avec MAC addresses
SELECT 
    COUNT(*) as total_detections,
    COUNT(DISTINCT device_mac_address) as unique_devices,
    COUNT(DISTINCT user_id) as identified_users
FROM presence
WHERE detected_at >= NOW() - INTERVAL '24 hours';
```

### Résultats Attendus

```
Users: 1 utilisateur (admin)
Raspberry Pi: 3 appareils (Salon, Chambre, Cuisine)
Devices: 8 appareils (3 salon + 3 chambre + 2 cuisine)
Rules: 3 règles d'automatisation
Training Data: ~27 échantillons
Light Readings: ~48 mesures (simulation 24h)
Presence: ~50 détections Bluetooth
Bluetooth Devices: 2 devices associés (exemple)
Events: 4 événements
Smart Dimming Adjustments: 3 ajustements
User Preferences: 0 (vide au départ)
```

---

## Configuration Backend

### Créer le Fichier .env

```bash
cd /chemin/vers/sae_s5/backend
cp .env.example .env
nano .env
```

### Contenu du Fichier .env

```env
# Configuration Base de Données
DATABASE_URL=postgresql://smarthome_user:votre_mot_de_passe@localhost:5432/smarthome

# Alternative pour développement (utilisateur postgres)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/smarthome

# Configuration JWT
SECRET_KEY=votre_cle_secrete_tres_longue_et_aleatoire_minimum_32_caracteres
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Configuration Serveur
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true
ENVIRONMENT=development

# Configuration CORS (pour application mobile)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://192.168.1.0/24
```

### Créer un Utilisateur Applicatif (Recommandé pour Production)

```sql
-- Se connecter en tant que postgres
sudo -u postgres psql

-- Créer l'utilisateur
CREATE USER smarthome_user WITH PASSWORD 'VotreMotDePasseSecurise123!';

-- Se connecter à la base smarthome
\c smarthome

-- Accorder les permissions
GRANT CONNECT ON DATABASE smarthome TO smarthome_user;
GRANT USAGE ON SCHEMA public TO smarthome_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO smarthome_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO smarthome_user;

-- Accorder les permissions sur les futures tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO smarthome_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO smarthome_user;

-- Quitter
\q
```

### Tester la Connexion Backend

```bash
# Activer l'environnement virtuel
cd /chemin/vers/sae_s5/backend
source venv/bin/activate

# Installer les dépendances (si pas déjà fait)
pip install -r requirements.txt

# Tester la connexion à la base
python -c "from app.database import engine; print('[OK] Connexion DB réussie')"

# Lancer le serveur
uvicorn app.main:app --reload
```

Ouvrir http://localhost:8000/docs pour voir la documentation Swagger.

---

## Commandes Utiles

### Gestion de PostgreSQL

```bash
# Démarrer le service
sudo systemctl start postgresql

# Arrêter le service
sudo systemctl stop postgresql

# Redémarrer le service
sudo systemctl restart postgresql

# Vérifier le statut
sudo systemctl status postgresql
```

### Commandes psql

```sql
-- Se connecter à la base
sudo -u postgres psql -d smarthome

-- Lister les bases de données
\l

-- Lister les tables
\dt

-- Lister les vues
\dv

-- Décrire une table
\d nom_table

-- Exécuter un fichier SQL
\i /chemin/vers/script.sql

-- Afficher l'aide
\?

-- Quitter
\q
```

### Sauvegardes et Restauration

```bash
# Créer une sauvegarde
sudo -u postgres pg_dump smarthome > backup_$(date +%Y%m%d_%H%M%S).sql

# Restaurer une sauvegarde
sudo -u postgres psql -d smarthome < backup_20250106_120000.sql

# Sauvegarde avec compression
sudo -u postgres pg_dump smarthome | gzip > backup.sql.gz

# Restauration depuis archive compressée
gunzip -c backup.sql.gz | sudo -u postgres psql -d smarthome
```

### Réinitialisation Complète

```bash
# ATTENTION : Supprime toutes les données !

# Se connecter à PostgreSQL
sudo -u postgres psql

# Supprimer et recréer la base
DROP DATABASE IF EXISTS smarthome;
\q

# Réexécuter le script d'initialisation
sudo -u postgres psql -f db/init_database.sql
```

---

## Dépannage

### Problème : "Peer authentication failed"

**Solution 1 : Modifier pg_hba.conf**

```bash
# Éditer le fichier de configuration
sudo nano /etc/postgresql/14/main/pg_hba.conf

# Changer la ligne :
# local   all   postgres   peer
# En :
# local   all   postgres   md5

# Redémarrer PostgreSQL
sudo systemctl restart postgresql
```

**Solution 2 : Définir un mot de passe pour postgres**

```bash
sudo -u postgres psql
ALTER USER postgres PASSWORD 'votre_mot_de_passe';
\q
```

### Problème : "Port 5432 already in use"

```bash
# Vérifier les processus utilisant le port
sudo lsof -i :5432

# Arrêter PostgreSQL proprement
sudo systemctl stop postgresql

# Si nécessaire, tuer le processus
sudo kill -9 <PID>

# Redémarrer
sudo systemctl start postgresql
```

### Problème : "Connection refused"

```bash
# Vérifier que PostgreSQL écoute sur le bon port
sudo netstat -tulpn | grep 5432

# Éditer postgresql.conf
sudo nano /etc/postgresql/14/main/postgresql.conf

# Vérifier la ligne :
listen_addresses = 'localhost'  # ou '*' pour écouter sur toutes les interfaces

# Redémarrer
sudo systemctl restart postgresql
```

### Problème : "Role does not exist"

```sql
-- Se connecter en tant que postgres
sudo -u postgres psql

-- Créer le rôle manquant
CREATE ROLE nom_utilisateur WITH LOGIN PASSWORD 'mot_de_passe';

-- Accorder les permissions
GRANT ALL PRIVILEGES ON DATABASE smarthome TO nom_utilisateur;
```

### Problème : "Permission denied for table"

```sql
-- Se connecter à la base
sudo -u postgres psql -d smarthome

-- Accorder les permissions manquantes
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO nom_utilisateur;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO nom_utilisateur;
```

### Problème : Backend ne se connecte pas à la base

```bash
# Vérifier la variable DATABASE_URL dans .env
cat .env | grep DATABASE_URL

# Tester la connexion manuellement
psql "postgresql://smarthome_user:password@localhost:5432/smarthome"

# Vérifier les logs PostgreSQL
sudo tail -f /var/log/postgresql/postgresql-14-main.log
```

---

## Requêtes Utiles

### Statistiques Générales

```sql
-- Nombre total d'appareils par type
SELECT type, COUNT(*) as count 
FROM devices 
GROUP BY type;

-- Raspberry Pi en ligne/hors ligne
SELECT 
    CASE WHEN is_online THEN 'En ligne' ELSE 'Hors ligne' END as status,
    COUNT(*) as count
FROM raspberry_pis
GROUP BY is_online;

-- Nombre de détections de présence Bluetooth aujourd'hui
SELECT COUNT(*) 
FROM presence 
WHERE detected_at::date = CURRENT_DATE;

-- Détections avec identification utilisateur
SELECT 
    COUNT(*) as total_detections,
    COUNT(DISTINCT device_mac_address) as unique_devices,
    COUNT(DISTINCT user_id) as identified_users
FROM presence 
WHERE detected_at::date = CURRENT_DATE;

-- Règles actives par priorité
SELECT name, priority, enabled 
FROM rules 
ORDER BY priority DESC;
```

### Historique des Événements

```sql
-- 10 derniers événements
SELECT 
    e.timestamp,
    d.name as device_name,
    e.event_type,
    e.value,
    e.source
FROM events e
LEFT JOIN devices d ON e.device_id = d.id
ORDER BY e.timestamp DESC
LIMIT 10;

-- Événements par source
SELECT 
    source,
    COUNT(*) as count,
    MAX(timestamp) as last_event
FROM events
GROUP BY source;
```

### Analyse de Présence Bluetooth

```sql
-- Détections par heure (dernières 24h)
SELECT 
    EXTRACT(HOUR FROM detected_at) as hour,
    COUNT(*) as detections
FROM presence
WHERE detected_at >= NOW() - INTERVAL '24 hours'
GROUP BY EXTRACT(HOUR FROM detected_at)
ORDER BY hour;

-- Détections par localisation (dernière semaine)
SELECT 
    r.location,
    COUNT(p.id) as detections
FROM presence p
JOIN raspberry_pis r ON p.raspberry_pi_id = r.id
WHERE p.detected_at >= NOW() - INTERVAL '7 days'
GROUP BY r.location
ORDER BY detections DESC;

-- Devices Bluetooth détectés avec force du signal
SELECT 
    device_mac_address,
    COUNT(*) as detection_count,
    AVG(signal_strength) as avg_rssi,
    MAX(detected_at) as last_seen
FROM presence
WHERE device_mac_address IS NOT NULL
    AND detected_at >= NOW() - INTERVAL '24 hours'
GROUP BY device_mac_address
ORDER BY detection_count DESC;

-- Détections par utilisateur (si MAC mappée)
SELECT 
    u.username,
    COUNT(p.id) as detections,
    AVG(p.signal_strength) as avg_rssi
FROM presence p
JOIN users u ON p.user_id = u.id
WHERE p.detected_at >= NOW() - INTERVAL '24 hours'
GROUP BY u.username
ORDER BY detections DESC;

-- Liste des devices Bluetooth associés aux utilisateurs
SELECT 
    u.username,
    bd.device_name,
    bd.mac_address,
    bd.device_type,
    bd.is_active
FROM bluetooth_devices bd
JOIN users u ON bd.user_id = u.id
ORDER BY u.username, bd.device_name;
```

### Analyse Smart Dimming

```sql
-- Efficacité du Smart Dimming par appareil
SELECT 
    d.name,
    COUNT(sda.id) as total_adjustments,
    AVG(ABS(sda.target_brightness - sda.previous_brightness)) as avg_change,
    MAX(sda.adjusted_at) as last_adjustment
FROM smart_dimming_adjustments sda
JOIN devices d ON sda.device_id = d.id
GROUP BY d.name
ORDER BY total_adjustments DESC;

-- Ajustements par scénario
SELECT 
    CASE scenario
        WHEN 0 THEN 'Day'
        WHEN 1 THEN 'Night'
        WHEN 2 THEN 'Away'
        WHEN 3 THEN 'Evening'
    END as scenario_name,
    COUNT(*) as count
FROM smart_dimming_adjustments
GROUP BY scenario;
```

---

## Schéma de Données

### Relations entre Tables

```
users (1) ----< (N) user_preferences
    |
    +-------< (N) bluetooth_devices

raspberry_pis (1) ----< (N) devices
    |
    +-------< (N) presence
    |           |
    |           +-----> (N) users (via user_id, optionnel)
    |
    +-------< (N) light_readings

devices (1) ----< (N) events
    |
    +-------< (N) smart_dimming_adjustments

light_readings (1) ----< (N) smart_dimming_adjustments

presence (N) ----< (1) bluetooth_devices (via device_mac_address, optionnel)

rules (standalone, références JSONB vers devices)
training_data (standalone, apprentissage automatique)
```

### Tables Principales

- **users** : Utilisateurs du système (authentification)
- **raspberry_pis** : Configuration des Raspberry Pi connectés
- **devices** : Appareils électriques (lampes, prises)
- **presence** : Historique des détections de présence via Bluetooth (remplace PIR)
  - `device_mac_address` : Adresse MAC du device détecté
  - `signal_strength` : Force du signal RSSI en dBm
  - `user_id` : ID utilisateur si MAC mappée dans `bluetooth_devices`
- **bluetooth_devices** : Association entre adresses MAC Bluetooth et utilisateurs
  - Permet d'identifier les personnes via leurs devices (téléphone, montre, etc.)
- **light_readings** : Mesures de luminosité ambiante (time-series)
- **rules** : Règles d'automatisation (format JSONB)
- **events** : Journal des événements système
- **smart_dimming_adjustments** : Historique des ajustements automatiques
- **training_data** : Données d'entraînement pour l'IA
- **user_preferences** : Préférences utilisateur pour apprentissage personnalisé

Pour plus de détails, voir le fichier `init_database.sql`.

---

## Sécurité

### Bonnes Pratiques

1. **Mots de passe forts** : Minimum 16 caractères, alphanumériques + symboles
2. **Utilisateur dédié** : Ne pas utiliser l'utilisateur `postgres` en production
3. **Restrictions réseau** : Limiter les connexions dans `pg_hba.conf`
4. **Sauvegardes régulières** : Automatiser les backups quotidiens
5. **Chiffrement** : Activer SSL pour les connexions distantes

### Configuration SSL (Optionnel)

```bash
# Générer un certificat auto-signé
sudo openssl req -new -x509 -days 365 -nodes -text \
  -out /etc/postgresql/14/main/server.crt \
  -keyout /etc/postgresql/14/main/server.key

# Modifier les permissions
sudo chmod 600 /etc/postgresql/14/main/server.key
sudo chown postgres:postgres /etc/postgresql/14/main/server.key

# Activer SSL dans postgresql.conf
sudo nano /etc/postgresql/14/main/postgresql.conf
# Décommenter et modifier :
ssl = on

# Redémarrer
sudo systemctl restart postgresql
```

---

## Ressources

- [Documentation PostgreSQL](https://www.postgresql.org/docs/14/)
- [Documentation TimescaleDB](https://docs.timescale.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [FastAPI Database](https://fastapi.tiangolo.com/tutorial/sql-databases/)
- [psycopg2 Documentation](https://www.psycopg.org/docs/)

---

## Notes Importantes

1. **Données de test** : Le script crée automatiquement un utilisateur admin avec le mot de passe `admin123` (à changer en production)
2. **API Keys** : Les clés API des Raspberry Pi sont générées automatiquement et doivent être copiées dans leur fichier de configuration
3. **Performance** : Les index sont créés automatiquement pour optimiser les requêtes fréquentes
4. **Vues** : Des vues SQL sont disponibles pour simplifier les requêtes courantes
5. **Triggers** : Les champs `updated_at` sont mis à jour automatiquement
6. **TimescaleDB** : L'extension est optionnelle mais recommandée pour optimiser les requêtes sur `light_readings` (time-series)

---

## Checklist de Validation

- [ ] PostgreSQL installé et démarré
- [ ] Base `smarthome` créée
- [ ] 11 tables créées (users, raspberry_pis, devices, presence, bluetooth_devices, etc.)
- [ ] Données de test insérées
- [ ] Vues créées (devices_with_location, etc.)
- [ ] Fonctions créées (get_device_state, etc.)
- [ ] Fichier .env configuré dans le backend
- [ ] Connexion backend testée
- [ ] Documentation Swagger accessible
- [ ] TimescaleDB activé (optionnel)

---

**Support** : En cas de problème, consulter les logs PostgreSQL :
```bash
sudo tail -f /var/log/postgresql/postgresql-14-main.log
```
