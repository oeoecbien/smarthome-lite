# Guide d'Initialisation Base de Données SmartHome Lite

## Table des Matières

1. [Prérequis](#prérequis)
2. [Installation PostgreSQL](#installation-postgresql)
3. [Initialisation de la Base](#initialisation-de-la-base)
4. [Vérification](#vérification)
5. [Configuration Backend](#configuration-backend)
6. [Commandes Utiles](#commandes-utiles)
7. [Dépannage](#dépannage)

---

## Prérequis

### Versions Requises
- **PostgreSQL** : 14.0 ou supérieur
- **Système** : Linux (Ubuntu/Debian recommandé) ou macOS
- **Droits** : Accès administrateur (sudo)

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
cd /chemin/vers/smarthome-backend/database

# Exécuter le script
sudo -u postgres psql -f init_database.sql
```

**Option B : Depuis psql interactif**

```sql
-- Dans le prompt psql
\i /chemin/vers/init_database.sql
```

### Étape 3 : Vérifier la Création

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
- `events`
- `rules`
- `training_data`

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
```

### Résultats Attendus

```
Users: 1 utilisateur (admin)
Raspberry Pi: 2 appareils (Salon, Chambre)
Devices: 7 appareils (4 salon + 3 chambre)
Rules: 3 règles d'automatisation
Training Data: ~20 échantillons
```

---

## Configuration Backend

### Créer le Fichier .env

```bash
cd /chemin/vers/smarthome-backend
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
HOST=0.0.0.0
PORT=8000
DEBUG=true

# Configuration CORS (pour application mobile)
CORS_ORIGINS=["http://localhost:3000","http://192.168.1.0/24"]
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

-- Quitter
\q
```

### Tester la Connexion Backend

```bash
# Activer l'environnement virtuel
cd /chemin/vers/smarthome-backend
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
sudo -u postgres psql -f init_database.sql
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

-- Nombre de détections de présence aujourd'hui
SELECT COUNT(*) 
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

### Analyse de Présence

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
```

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

---

## Checklist de Validation

- [ ] PostgreSQL installé et démarré
- [ ] Base `smarthome` créée
- [ ] 7 tables créées (users, raspberry_pis, devices, etc.)
- [ ] Données de test insérées
- [ ] Vues créées (devices_with_location, etc.)
- [ ] Fichier .env configuré dans le backend
- [ ] Connexion backend testée
- [ ] Documentation Swagger accessible

---

**Support** : En cas de problème, consulter les logs PostgreSQL :
```bash
sudo tail -f /var/log/postgresql/postgresql-14-main.log
```