# Scripts de Configuration et Reconstruction de la Base de Données

Ces scripts permettent de configurer PostgreSQL et de recréer complètement la base de données pour le projet SmartHome.

## Configuration

Les scripts utilisent les paramètres suivants :

- **Host**: 10.109.150.75
- **Port**: 5432
- **Database**: smarthome
- **User**: postgres
- **Password**: smarthome2025

## Utilisation Rapide (Recommandé)

Pour tout configurer automatiquement en une seule commande :

```bash
./sae_s5/db/setup_complete.sh
```

Ce script fait tout automatiquement :
1. Configure PostgreSQL pour accepter les connexions distantes
2. Configure le mot de passe de l'utilisateur postgres
3. Supprime et recrée la base de données
4. Initialise toutes les tables, vues, fonctions et données de test

## Utilisation Manuelle

Si vous préférez exécuter les étapes séparément :

### 1. Configuration PostgreSQL (première fois uniquement)

```bash
sudo ./sae_s5/db/configure_postgresql.sh
```

Ce script configure :
- `listen_addresses` pour accepter les connexions réseau
- `pg_hba.conf` pour autoriser les connexions distantes
- Redémarre PostgreSQL

### 2. Reconstruction de la base de données

```bash
./sae_s5/db/recreate_database.sh
```

## Scripts Disponibles

| Script | Description | Nécessite sudo |
|--------|-------------|----------------|
| `setup_complete.sh` | **Recommandé** : Configure tout automatiquement | Oui |
| `configure_postgresql.sh` | Configure PostgreSQL pour accepter les connexions distantes | Oui |
| `recreate_database.sh` | Supprime et recrée la base de données avec toutes les tables | Non |

## Prérequis

1. **PostgreSQL installé** : PostgreSQL 15 doit être installé sur la machine
2. **Accès root/sudo** : Pour la configuration initiale de PostgreSQL
3. **PostgreSQL client** : Le client `psql` doit être installé

## Vérifications du Serveur PostgreSQL

Si la connexion échoue, vérifiez sur le serveur PostgreSQL :

### 1. Configuration PostgreSQL (`postgresql.conf`)
```conf
listen_addresses = '*'  # ou l'IP spécifique
port = 5432
```

### 2. Authentification (`pg_hba.conf`)
Ajoutez une ligne pour autoriser les connexions :
```
host    all             all             0.0.0.0/0               md5
# ou pour une IP spécifique :
host    all             all             10.109.150.0/24          md5
```

### 3. Redémarrer PostgreSQL
```bash
sudo systemctl restart postgresql
# ou
sudo service postgresql restart
```

### 4. Vérifier le firewall
Assurez-vous que le port 5432 est ouvert :
```bash
sudo ufw allow 5432/tcp
# ou
sudo iptables -A INPUT -p tcp --dport 5432 -j ACCEPT
```

## Ce que fait le script

1. **Test de connexion** : Vérifie que le serveur PostgreSQL est accessible
2. **Suppression** : Supprime la base de données `smarthome` si elle existe
3. **Création** : Crée une nouvelle base de données avec l'encodage UTF-8
4. **Initialisation** : Exécute le script `init_database.sql` qui crée :
   - Toutes les tables (users, devices, raspberry_pis, etc.)
     - Table `users` inclut les champs `reset_token` et `reset_token_expires` pour la réinitialisation de mot de passe
   - Les index pour optimiser les performances (y compris index sur `reset_token` pour les recherches rapides)
   - Les triggers pour la mise à jour automatique
   - Les vues utiles
   - Les fonctions SQL
   - Les données de test

## Structure de la table `users`

La table `users` inclut les champs suivants pour la réinitialisation de mot de passe :
- `reset_token` : Token de réinitialisation généré avec `secrets.token_urlsafe()` (VARCHAR(255), nullable)
- `reset_token_expires` : Date d'expiration du token (généralement 1 heure après génération, TIMESTAMP WITH TIME ZONE, nullable)

Un index est créé sur `reset_token` (`idx_users_reset_token`) pour optimiser les recherches lors de la validation des tokens de réinitialisation.

## Avertissement

**ATTENTION** : Ce script supprime toutes les données existantes dans la base de données `smarthome`. Utilisez-le uniquement en développement ou après avoir fait une sauvegarde en production.

## Alternative : Exécution manuelle

Si le script ne fonctionne pas, vous pouvez exécuter manuellement :

```bash
# 1. Se connecter au serveur PostgreSQL
export PGPASSWORD="smarthome2025"
psql -h 10.109.150.75 -p 5432 -U postgres -d postgres

# 2. Dans psql, supprimer et recréer la base
DROP DATABASE IF EXISTS smarthome;
CREATE DATABASE smarthome WITH OWNER = postgres ENCODING = 'UTF8' LC_COLLATE = 'fr_FR.UTF-8' LC_CTYPE = 'fr_FR.UTF-8' TEMPLATE = template0;
\q

# 3. Exécuter le script d'initialisation (sans les lignes 1-23)
psql -h 10.109.150.75 -p 5432 -U postgres -d smarthome -f sae_s5/db/init_database.sql
```
