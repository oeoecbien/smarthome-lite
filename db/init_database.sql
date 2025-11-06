-- ============================================================================
-- SmartHome Lite - Script d'Initialisation Base de Données
-- ============================================================================

-- ============================================================================
-- 1. CRÉATION DE LA BASE DE DONNÉES
-- ============================================================================

-- Supprimer la base si elle existe déjà (ATTENTION: supprime toutes les données)
DROP DATABASE IF EXISTS smarthome;

-- Créer la base de données avec encodage UTF-8
CREATE DATABASE smarthome
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'fr_FR.UTF-8'
    LC_CTYPE = 'fr_FR.UTF-8'
    TEMPLATE = template0;

-- Se connecter à la base de données
\c smarthome

-- ============================================================================
-- 2. CRÉATION DES TABLES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Table: users
-- Description: Gestion des utilisateurs du système
-- ----------------------------------------------------------------------------
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour recherche rapide par username
CREATE INDEX idx_users_username ON users(username);

-- ----------------------------------------------------------------------------
-- Table: raspberry_pis
-- Description: Inventaire des Raspberry Pi connectés
-- ----------------------------------------------------------------------------
CREATE TABLE raspberry_pis (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    ip_address VARCHAR(15) UNIQUE NOT NULL,
    location VARCHAR(100),
    is_online BOOLEAN DEFAULT FALSE,
    api_key VARCHAR(64) UNIQUE NOT NULL,
    last_heartbeat TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour recherche rapide par API key
CREATE INDEX idx_raspberry_pis_api_key ON raspberry_pis(api_key);

-- ----------------------------------------------------------------------------
-- Table: devices
-- Description: Référentiel des appareils connectés (lampes, prises, capteurs)
-- ----------------------------------------------------------------------------
CREATE TABLE devices (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('light', 'outlet', 'sensor')),
    raspberry_pi_id INTEGER NOT NULL REFERENCES raspberry_pis(id) ON DELETE CASCADE,
    gpio_pin INTEGER NOT NULL,
    state BOOLEAN DEFAULT FALSE,
    brightness INTEGER CHECK (brightness BETWEEN 0 AND 100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(raspberry_pi_id, gpio_pin),
    CONSTRAINT brightness_for_lights_only CHECK (
        (type = 'light' AND brightness IS NOT NULL) OR 
        (type != 'light' AND brightness IS NULL)
    )
);

-- Index pour recherche par type et Raspberry Pi
CREATE INDEX idx_devices_type ON devices(type);
CREATE INDEX idx_devices_raspberry_pi ON devices(raspberry_pi_id);

-- ----------------------------------------------------------------------------
-- Table: presence
-- Description: Historique des détections de mouvement
-- ----------------------------------------------------------------------------
CREATE TABLE presence (
    id SERIAL PRIMARY KEY,
    raspberry_pi_id INTEGER NOT NULL REFERENCES raspberry_pis(id) ON DELETE CASCADE,
    detected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Index pour recherche par date et par Raspberry Pi
CREATE INDEX idx_presence_detected_at ON presence(detected_at DESC);
CREATE INDEX idx_presence_raspberry_pi ON presence(raspberry_pi_id);

-- ----------------------------------------------------------------------------
-- Table: events
-- Description: Journal des événements système (actions, changements d'état)
-- ----------------------------------------------------------------------------
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    device_id INTEGER REFERENCES devices(id) ON DELETE SET NULL,
    event_type VARCHAR(50) NOT NULL,
    value VARCHAR(100),
    source VARCHAR(20) CHECK (source IN ('manual', 'automatic', 'ai', 'system')),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour recherche par device, type et date
CREATE INDEX idx_events_device_id ON events(device_id);
CREATE INDEX idx_events_timestamp ON events(timestamp DESC);
CREATE INDEX idx_events_source ON events(source);

-- ----------------------------------------------------------------------------
-- Table: rules
-- Description: Définition des règles d'automatisation IF-THEN
-- ----------------------------------------------------------------------------
CREATE TABLE rules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    enabled BOOLEAN DEFAULT TRUE,
    condition JSONB NOT NULL,
    action JSONB NOT NULL,
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour recherche de règles actives et par priorité
CREATE INDEX idx_rules_enabled ON rules(enabled);
CREATE INDEX idx_rules_priority ON rules(priority DESC);

-- Index GIN pour recherche dans les champs JSONB
CREATE INDEX idx_rules_condition ON rules USING GIN (condition);
CREATE INDEX idx_rules_action ON rules USING GIN (action);

-- ----------------------------------------------------------------------------
-- Table: training_data
-- Description: Données d'entraînement pour l'algorithme de classification IA
-- ----------------------------------------------------------------------------
CREATE TABLE training_data (
    id SERIAL PRIMARY KEY,
    hour INTEGER NOT NULL CHECK (hour BETWEEN 0 AND 23),
    day_of_week INTEGER NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    presence_detected BOOLEAN NOT NULL,
    light_on BOOLEAN NOT NULL,
    scenario INTEGER NOT NULL CHECK (scenario BETWEEN 0 AND 3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour analyse de données
CREATE INDEX idx_training_data_scenario ON training_data(scenario);
CREATE INDEX idx_training_data_hour ON training_data(hour);

-- ============================================================================
-- 3. CRÉATION DES FONCTIONS TRIGGERS
-- ============================================================================

-- Fonction pour mettre à jour automatiquement le champ updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Appliquer le trigger sur les tables avec updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_raspberry_pis_updated_at BEFORE UPDATE ON raspberry_pis
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_devices_updated_at BEFORE UPDATE ON devices
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_rules_updated_at BEFORE UPDATE ON rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 4. INSERTION DE DONNÉES DE TEST
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Utilisateur de test
-- ----------------------------------------------------------------------------
-- Mot de passe: "admin123" (haché avec bcrypt, cost=12)
INSERT INTO users (username, email, password_hash) VALUES
('admin', 'admin@smarthome.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzpLaEZU.O');

-- ----------------------------------------------------------------------------
-- Raspberry Pi de test
-- ----------------------------------------------------------------------------
INSERT INTO raspberry_pis (name, ip_address, location, is_online, api_key) VALUES
('RPi-Salon', '192.168.1.100', 'Salon', TRUE, 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2'),
('RPi-Chambre', '192.168.1.101', 'Chambre', TRUE, 'b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2g3');

-- ----------------------------------------------------------------------------
-- Appareils de test
-- ----------------------------------------------------------------------------
-- Appareils du Salon (RPi-Salon)
INSERT INTO devices (name, type, raspberry_pi_id, gpio_pin, state, brightness) VALUES
('Lampe Salon Principal', 'light', 1, 18, FALSE, 0),
('Lampe Salon Ambiance', 'light', 1, 23, FALSE, 0),
('Prise TV', 'outlet', 1, 24, FALSE, NULL),
('Capteur PIR Salon', 'sensor', 1, 4, FALSE, NULL);

-- Appareils de la Chambre (RPi-Chambre)
INSERT INTO devices (name, type, raspberry_pi_id, gpio_pin, state, brightness) VALUES
('Lampe Chevet', 'light', 2, 18, FALSE, 0),
('Prise Chargeurs', 'outlet', 2, 23, FALSE, NULL),
('Capteur PIR Chambre', 'sensor', 2, 4, FALSE, NULL);

-- ----------------------------------------------------------------------------
-- Règles d'automatisation de test
-- ----------------------------------------------------------------------------

-- Règle 1: Allumer la lampe du salon en soirée si présence détectée
INSERT INTO rules (name, description, enabled, condition, action, priority) VALUES
(
    'Éclairage Salon Soirée',
    'Allume automatiquement la lampe du salon à 70% en soirée si présence détectée',
    TRUE,
    '{
        "type": "AND",
        "conditions": [
            {"type": "presence", "location": "Salon", "value": true},
            {"type": "time_range", "start": "18:00", "end": "23:00"}
        ]
    }',
    '{
        "type": "device_control",
        "device_id": 1,
        "action": "turn_on",
        "brightness": 70
    }',
    10
);

-- Règle 2: Éteindre toutes les lampes après 10 minutes sans présence
INSERT INTO rules (name, description, enabled, condition, action, priority) VALUES
(
    'Économie Énergie',
    'Éteint automatiquement toutes les lampes après 10 minutes sans détection de présence',
    TRUE,
    '{
        "type": "no_presence_duration",
        "duration_minutes": 10
    }',
    '{
        "type": "all_lights_off"
    }',
    5
);

-- Règle 3: Mode nuit - éclairage minimal
INSERT INTO rules (name, description, enabled, condition, action, priority) VALUES
(
    'Mode Nuit',
    'Active un éclairage minimal (20%) la nuit si présence détectée',
    TRUE,
    '{
        "type": "AND",
        "conditions": [
            {"type": "presence", "value": true},
            {"type": "time_range", "start": "23:00", "end": "06:00"}
        ]
    }',
    '{
        "type": "device_control",
        "device_id": 1,
        "action": "turn_on",
        "brightness": 20
    }',
    15
);

-- ----------------------------------------------------------------------------
-- Données d'entraînement IA (échantillon)
-- ----------------------------------------------------------------------------

-- Scénarios: 0=Day, 1=Night, 2=Away, 3=Evening

-- Données pour scénario "Day" (journée normale)
INSERT INTO training_data (hour, day_of_week, presence_detected, light_on, scenario) VALUES
(9, 1, TRUE, FALSE, 0),
(10, 2, TRUE, FALSE, 0),
(11, 3, TRUE, FALSE, 0),
(12, 4, TRUE, FALSE, 0),
(14, 5, TRUE, FALSE, 0),
(15, 1, TRUE, FALSE, 0);

-- Données pour scénario "Evening" (soirée)
INSERT INTO training_data (hour, day_of_week, presence_detected, light_on, scenario) VALUES
(18, 1, TRUE, TRUE, 3),
(19, 2, TRUE, TRUE, 3),
(20, 3, TRUE, TRUE, 3),
(21, 4, TRUE, TRUE, 3),
(22, 5, TRUE, TRUE, 3);

-- Données pour scénario "Night" (nuit)
INSERT INTO training_data (hour, day_of_week, presence_detected, light_on, scenario) VALUES
(23, 1, TRUE, TRUE, 1),
(0, 2, FALSE, FALSE, 1),
(1, 3, FALSE, FALSE, 1),
(2, 4, FALSE, FALSE, 1),
(3, 5, FALSE, FALSE, 1),
(5, 1, FALSE, FALSE, 1);

-- Données pour scénario "Away" (absence)
INSERT INTO training_data (hour, day_of_week, presence_detected, light_on, scenario) VALUES
(10, 1, FALSE, FALSE, 2),
(14, 2, FALSE, FALSE, 2),
(16, 3, FALSE, FALSE, 2),
(11, 4, FALSE, FALSE, 2),
(15, 5, FALSE, FALSE, 2);

-- ============================================================================
-- 5. CRÉATION DES VUES UTILES
-- ============================================================================

-- Vue: devices_with_location
-- Affiche les appareils avec leur localisation (via Raspberry Pi)
CREATE VIEW devices_with_location AS
SELECT 
    d.id,
    d.name,
    d.type,
    d.state,
    d.brightness,
    d.gpio_pin,
    r.name AS raspberry_pi_name,
    r.location,
    r.is_online AS raspberry_pi_online
FROM devices d
JOIN raspberry_pis r ON d.raspberry_pi_id = r.id;

-- Vue: presence_last_24h
-- Affiche les détections de présence des dernières 24 heures
CREATE VIEW presence_last_24h AS
SELECT 
    p.id,
    p.detected_at,
    r.name AS raspberry_pi_name,
    r.location
FROM presence p
JOIN raspberry_pis r ON p.raspberry_pi_id = r.id
WHERE p.detected_at >= NOW() - INTERVAL '24 hours'
ORDER BY p.detected_at DESC;

-- Vue: active_rules
-- Affiche uniquement les règles actives triées par priorité
CREATE VIEW active_rules AS
SELECT 
    id,
    name,
    description,
    condition,
    action,
    priority
FROM rules
WHERE enabled = TRUE
ORDER BY priority DESC;

-- ============================================================================
-- 6. CRÉATION DES FONCTIONS UTILITAIRES
-- ============================================================================

-- Fonction: get_device_state
-- Retourne l'état actuel d'un appareil
CREATE OR REPLACE FUNCTION get_device_state(device_id_param INTEGER)
RETURNS TABLE (
    device_name VARCHAR,
    device_type VARCHAR,
    is_on BOOLEAN,
    current_brightness INTEGER,
    location VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        d.name,
        d.type,
        d.state,
        d.brightness,
        r.location
    FROM devices d
    JOIN raspberry_pis r ON d.raspberry_pi_id = r.id
    WHERE d.id = device_id_param;
END;
$$ LANGUAGE plpgsql;

-- Fonction: get_presence_count_by_hour
-- Compte le nombre de détections par heure pour une période donnée
CREATE OR REPLACE FUNCTION get_presence_count_by_hour(
    location_param VARCHAR,
    start_date TIMESTAMP,
    end_date TIMESTAMP
)
RETURNS TABLE (
    hour_of_day INTEGER,
    detection_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        EXTRACT(HOUR FROM p.detected_at)::INTEGER AS hour_of_day,
        COUNT(*)::BIGINT AS detection_count
    FROM presence p
    JOIN raspberry_pis r ON p.raspberry_pi_id = r.id
    WHERE r.location = location_param
        AND p.detected_at BETWEEN start_date AND end_date
    GROUP BY EXTRACT(HOUR FROM p.detected_at)
    ORDER BY hour_of_day;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 7. PERMISSIONS (OPTIONNEL)
-- ============================================================================

-- Créer un utilisateur applicatif avec permissions limitées
-- CREATE USER smarthome_app WITH PASSWORD 'votre_mot_de_passe_securise';
-- GRANT CONNECT ON DATABASE smarthome TO smarthome_app;
-- GRANT USAGE ON SCHEMA public TO smarthome_app;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO smarthome_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO smarthome_app;

-- ============================================================================
-- 8. AFFICHAGE DES STATISTIQUES
-- ============================================================================

-- Afficher un résumé de l'initialisation
SELECT 'Base de données initialisée avec succès!' AS status;

SELECT 
    'Utilisateurs' AS table_name, 
    COUNT(*) AS row_count 
FROM users
UNION ALL
SELECT 'Raspberry Pi', COUNT(*) FROM raspberry_pis
UNION ALL
SELECT 'Appareils', COUNT(*) FROM devices
UNION ALL
SELECT 'Règles', COUNT(*) FROM rules
UNION ALL
SELECT 'Données IA', COUNT(*) FROM training_data;

-- ============================================================================
-- FIN DU SCRIPT
-- ============================================================================