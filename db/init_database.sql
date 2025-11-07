-- ============================================================================
-- SmartHome Lite - Script d'Initialisation Base de Données
-- Version finale conforme au document technique
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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index pour recherche rapide par username (connexion fréquente)
CREATE INDEX idx_users_username ON users(username);

COMMENT ON TABLE users IS 'Utilisateurs du système SmartHome';
COMMENT ON COLUMN users.password_hash IS 'Hash bcrypt du mot de passe (12 rounds minimum)';
COMMENT ON COLUMN users.username IS 'Nom d''utilisateur unique pour connexion';

-- ----------------------------------------------------------------------------
-- Table: raspberry_pis
-- Description: Configuration des Raspberry Pi dans le réseau
-- ----------------------------------------------------------------------------
CREATE TABLE raspberry_pis (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    location VARCHAR(100) NOT NULL,
    ip_address VARCHAR(15),
    api_key VARCHAR(64) UNIQUE NOT NULL,
    is_online BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index pour recherche par localisation et état
CREATE INDEX idx_raspberry_pis_location ON raspberry_pis(location);
CREATE INDEX idx_raspberry_pis_online ON raspberry_pis(is_online);

COMMENT ON TABLE raspberry_pis IS 'Raspberry Pi déployés dans l''habitat';
COMMENT ON COLUMN raspberry_pis.api_key IS 'Clé d''authentification unique pour communication sécurisée';
COMMENT ON COLUMN raspberry_pis.is_online IS 'État de connexion (heartbeat toutes les 30s)';

-- ----------------------------------------------------------------------------
-- Table: devices
-- Description: Appareils connectés (lampes, prises, etc.)
-- ----------------------------------------------------------------------------
CREATE TABLE devices (
    id SERIAL PRIMARY KEY,
    raspberry_pi_id INTEGER NOT NULL REFERENCES raspberry_pis(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('light', 'socket', 'dimmer')),
    state BOOLEAN DEFAULT FALSE,
    brightness INTEGER DEFAULT 0 CHECK (brightness BETWEEN 0 AND 100),
    gpio_pin INTEGER NOT NULL CHECK (gpio_pin BETWEEN 1 AND 40),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(raspberry_pi_id, gpio_pin)
);

-- Index pour requêtes fréquentes (liste par emplacement, par type)
CREATE INDEX idx_devices_raspberry_pi ON devices(raspberry_pi_id);
CREATE INDEX idx_devices_type ON devices(type);
CREATE INDEX idx_devices_state ON devices(state);

COMMENT ON TABLE devices IS 'Appareils électriques contrôlables';
COMMENT ON COLUMN devices.gpio_pin IS 'Pin GPIO physique sur le Raspberry Pi (unique par RPi)';
COMMENT ON COLUMN devices.brightness IS 'Intensité lumineuse pour les dimmers (0-100)';

-- ----------------------------------------------------------------------------
-- Table: light_readings
-- Description: Mesures de luminosité ambiante
-- Nouvelle table pour le Smart Dimming
-- ----------------------------------------------------------------------------
CREATE TABLE light_readings (
    id SERIAL PRIMARY KEY,
    raspberry_pi_id INTEGER NOT NULL REFERENCES raspberry_pis(id) ON DELETE CASCADE,
    lux_value REAL NOT NULL CHECK (lux_value >= 0),
    sensor_type VARCHAR(20) NOT NULL DEFAULT 'BH1750' CHECK (sensor_type IN ('BH1750', 'LDR')),
    measured_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Index pour requêtes temporelles (graphiques, tendances)
CREATE INDEX idx_light_readings_measured_at ON light_readings(measured_at DESC);
CREATE INDEX idx_light_readings_raspberry_pi ON light_readings(raspberry_pi_id);

COMMENT ON TABLE light_readings IS 'Historique des mesures de luminosité ambiante';
COMMENT ON COLUMN light_readings.lux_value IS 'Intensité lumineuse en lux (0-65535 pour BH1750)';

-- ----------------------------------------------------------------------------
-- Table: presence
-- Description: Historique des détections de mouvement
-- ----------------------------------------------------------------------------
CREATE TABLE presence (
    id SERIAL PRIMARY KEY,
    raspberry_pi_id INTEGER NOT NULL REFERENCES raspberry_pis(id) ON DELETE CASCADE,
    detected_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Index pour recherche par date et par Raspberry Pi
CREATE INDEX idx_presence_detected_at ON presence(detected_at DESC);
CREATE INDEX idx_presence_raspberry_pi ON presence(raspberry_pi_id);

COMMENT ON TABLE presence IS 'Journal des détections PIR (mouvement/présence)';

-- ----------------------------------------------------------------------------
-- Table: rules
-- Description: Règles d'automatisation définies par l'utilisateur
-- ----------------------------------------------------------------------------
CREATE TABLE rules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    enabled BOOLEAN DEFAULT TRUE,
    condition JSONB NOT NULL,
    action JSONB NOT NULL,
    priority INTEGER DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index pour recherche des règles actives et tri par priorité
CREATE INDEX idx_rules_enabled ON rules(enabled);
CREATE INDEX idx_rules_priority ON rules(priority DESC);

COMMENT ON TABLE rules IS 'Règles d''automatisation (format JSON pour flexibilité)';
COMMENT ON COLUMN rules.condition IS 'Conditions d''activation (JSON: type, value, operators)';
COMMENT ON COLUMN rules.action IS 'Action à exécuter (JSON: type, device_id, parameters)';
COMMENT ON COLUMN rules.priority IS '1=basse, 10=haute (ordre d''évaluation)';

-- ----------------------------------------------------------------------------
-- Table: events
-- Description: Journal des événements système (actions, changements d'état)
-- ----------------------------------------------------------------------------
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    device_id INTEGER REFERENCES devices(id) ON DELETE SET NULL,
    event_type VARCHAR(50) NOT NULL,
    value VARCHAR(100),
    source VARCHAR(20) CHECK (source IS NULL OR source IN ('manual', 'automatic', 'ai', 'system', 'smart_dimming')),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Index pour recherche par device, type et date
CREATE INDEX idx_events_device_id ON events(device_id);
CREATE INDEX idx_events_timestamp ON events(timestamp DESC);
CREATE INDEX idx_events_source ON events(source);
CREATE INDEX idx_events_event_type ON events(event_type);

COMMENT ON TABLE events IS 'Audit trail de toutes les actions système';
COMMENT ON COLUMN events.source IS 'Origine de l''événement (ajout "smart_dimming")';

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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index pour analyse de données
CREATE INDEX idx_training_data_scenario ON training_data(scenario);
CREATE INDEX idx_training_data_hour ON training_data(hour);

COMMENT ON TABLE training_data IS 'Dataset pour entraînement Decision Tree (4 scénarios)';
COMMENT ON COLUMN training_data.scenario IS '0=Day, 1=Night, 2=Away, 3=Evening';

-- ----------------------------------------------------------------------------
-- Table: smart_dimming_adjustments
-- Description: Historique des ajustements automatiques d'intensité
-- Nouvelle table pour traçabilité Smart Dimming
-- ----------------------------------------------------------------------------
CREATE TABLE smart_dimming_adjustments (
    id SERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    light_reading_id INTEGER REFERENCES light_readings(id) ON DELETE SET NULL,
    scenario INTEGER NOT NULL CHECK (scenario BETWEEN 0 AND 3),
    previous_brightness INTEGER NOT NULL CHECK (previous_brightness BETWEEN 0 AND 100),
    target_brightness INTEGER NOT NULL CHECK (target_brightness BETWEEN 0 AND 100),
    applied_brightness INTEGER NOT NULL CHECK (applied_brightness BETWEEN 0 AND 100),
    reason VARCHAR(200),
    adjusted_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Index pour analyse des ajustements
CREATE INDEX idx_dimming_device ON smart_dimming_adjustments(device_id);
CREATE INDEX idx_dimming_adjusted_at ON smart_dimming_adjustments(adjusted_at DESC);
CREATE INDEX idx_dimming_scenario ON smart_dimming_adjustments(scenario);

COMMENT ON TABLE smart_dimming_adjustments IS 'Enregistre chaque ajustement automatique pour analyse';
COMMENT ON COLUMN smart_dimming_adjustments.reason IS 'Justification textuelle (ex: "High natural light")';
COMMENT ON COLUMN smart_dimming_adjustments.target_brightness IS 'Intensité calculée par l''algorithme';
COMMENT ON COLUMN smart_dimming_adjustments.applied_brightness IS 'Intensité réellement appliquée (peut différer)';

-- ----------------------------------------------------------------------------
-- Table: user_preferences
-- Description: Apprentissage des préférences utilisateur
-- Nouvelle table pour personnalisation future
-- ----------------------------------------------------------------------------
CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    light_level REAL NOT NULL CHECK (light_level >= 0),
    scenario INTEGER NOT NULL CHECK (scenario BETWEEN 0 AND 3),
    auto_brightness INTEGER NOT NULL CHECK (auto_brightness BETWEEN 0 AND 100),
    manual_brightness INTEGER NOT NULL CHECK (manual_brightness BETWEEN 0 AND 100),
    time_of_day INTEGER NOT NULL CHECK (time_of_day BETWEEN 0 AND 23),
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Index pour analyse des préférences
CREATE INDEX idx_preferences_user ON user_preferences(user_id);
CREATE INDEX idx_preferences_device ON user_preferences(device_id);
CREATE INDEX idx_preferences_scenario ON user_preferences(scenario);

COMMENT ON TABLE user_preferences IS 'Capture les ajustements manuels pour apprentissage personnalisé';
COMMENT ON COLUMN user_preferences.auto_brightness IS 'Intensité proposée par le système';
COMMENT ON COLUMN user_preferences.manual_brightness IS 'Intensité choisie par l''utilisateur (feedback)';

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

COMMENT ON FUNCTION update_updated_at_column() IS 'Trigger générique pour mise à jour automatique de updated_at';

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
-- 4. INSERTION DES DONNÉES DE TEST
-- ============================================================================

-- Utilisateur administrateur (mot de passe: admin123)
-- Hash bcrypt généré avec 12 rounds
INSERT INTO users (username, email, password_hash) VALUES
('admin', 'admin@smarthome.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYL3ZOE7jiq');

-- Note: Utilisateur de test: admin / admin123 (CHANGER EN PRODUCTION)

-- Configuration des Raspberry Pi
INSERT INTO raspberry_pis (name, location, ip_address, api_key, is_online) VALUES
('RPi-Salon', 'Salon', '192.168.1.101', 'rpi_salon_key_' || MD5(random()::text), TRUE),
('RPi-Chambre', 'Chambre', '192.168.1.102', 'rpi_chambre_key_' || MD5(random()::text), TRUE),
('RPi-Cuisine', 'Cuisine', '192.168.1.103', 'rpi_cuisine_key_' || MD5(random()::text), FALSE);

-- Appareils connectés
INSERT INTO devices (raspberry_pi_id, name, type, state, brightness, gpio_pin) VALUES
-- Salon
(1, 'Lampe Principale Salon', 'dimmer', TRUE, 75, 17),
(1, 'Lampe d''Appoint Salon', 'light', FALSE, 0, 18),
(1, 'Prise TV Salon', 'socket', TRUE, 100, 27),

-- Chambre
(2, 'Lampe Chevet Gauche', 'dimmer', FALSE, 50, 22),
(2, 'Lampe Chevet Droit', 'dimmer', FALSE, 50, 23),
(2, 'Prise Chargeurs', 'socket', TRUE, 100, 24),

-- Cuisine
(3, 'Plafonnier Cuisine', 'dimmer', TRUE, 100, 5),
(3, 'Hotte Cuisine', 'socket', FALSE, 100, 6);

-- Mesures de luminosité (simulation des dernières 24h)
-- Insertion de valeurs réalistes par tranches horaires
INSERT INTO light_readings (raspberry_pi_id, lux_value, sensor_type, measured_at) 
SELECT 
    1, -- RPi Salon
    CASE 
        WHEN EXTRACT(HOUR FROM ts) BETWEEN 0 AND 5 THEN 0 + random() * 10
        WHEN EXTRACT(HOUR FROM ts) BETWEEN 6 AND 8 THEN 50 + random() * 100
        WHEN EXTRACT(HOUR FROM ts) BETWEEN 9 AND 17 THEN 200 + random() * 500
        WHEN EXTRACT(HOUR FROM ts) BETWEEN 18 AND 20 THEN 100 + random() * 200
        ELSE 20 + random() * 50
    END,
    'BH1750',
    ts
FROM generate_series(
    NOW() - INTERVAL '24 hours',
    NOW(),
    INTERVAL '30 minutes'
) AS ts;

-- Détections de présence (simulation activité quotidienne)
INSERT INTO presence (raspberry_pi_id, detected_at)
SELECT 
    (ARRAY[1, 2])[floor(random() * 2 + 1)], -- Alternance Salon/Chambre
    NOW() - (random() * INTERVAL '24 hours')
FROM generate_series(1, 50);

-- Règles d'automatisation pré-configurées
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
),
(
    'Économie Énergie Nuit',
    'Éteint toutes les lampes après 10 minutes sans détection de présence',
    TRUE,
    '{
        "type": "no_presence_duration",
        "duration_minutes": 10
    }',
    '{
        "type": "all_lights_off"
    }',
    5
),
(
    'Smart Dimming Matin',
    'Ajuste automatiquement l''éclairage selon la luminosité naturelle le matin',
    TRUE,
    '{
        "type": "AND",
        "conditions": [
            {"type": "time_range", "start": "06:00", "end": "09:00"},
            {"type": "light_level", "operator": ">", "value": 100}
        ]
    }',
    '{
        "type": "smart_dimming",
        "target_devices": [1, 7]
    }',
    8
);

-- Événements récents (historique simulation)
INSERT INTO events (device_id, event_type, value, source, timestamp) VALUES
(1, 'brightness_changed', '75', 'smart_dimming', NOW() - INTERVAL '10 minutes'),
(1, 'state_changed', 'true', 'automatic', NOW() - INTERVAL '2 hours'),
(3, 'state_changed', 'true', 'manual', NOW() - INTERVAL '3 hours'),
(7, 'brightness_changed', '100', 'ai', NOW() - INTERVAL '5 hours');

-- Données d'entraînement IA (dataset équilibré pour 4 scénarios)
-- Scénario 0: Day (journée active)
INSERT INTO training_data (hour, day_of_week, presence_detected, light_on, scenario) VALUES
(8, 1, TRUE, TRUE, 0),
(9, 2, TRUE, TRUE, 0),
(10, 3, TRUE, FALSE, 0),
(11, 4, TRUE, TRUE, 0),
(12, 5, TRUE, FALSE, 0),
(13, 1, TRUE, TRUE, 0),
(14, 2, TRUE, FALSE, 0),
(15, 3, TRUE, TRUE, 0),
(16, 4, TRUE, FALSE, 0),
(17, 5, TRUE, TRUE, 0);

-- Scénario 1: Night (nuit)
INSERT INTO training_data (hour, day_of_week, presence_detected, light_on, scenario) VALUES
(23, 1, TRUE, TRUE, 1),
(0, 2, FALSE, FALSE, 1),
(1, 3, FALSE, FALSE, 1),
(2, 4, FALSE, FALSE, 1),
(3, 5, FALSE, FALSE, 1),
(4, 6, FALSE, FALSE, 1),
(5, 0, FALSE, FALSE, 1);

-- Scénario 2: Away (absence)
INSERT INTO training_data (hour, day_of_week, presence_detected, light_on, scenario) VALUES
(10, 1, FALSE, FALSE, 2),
(11, 2, FALSE, FALSE, 2),
(14, 3, FALSE, FALSE, 2),
(15, 4, FALSE, FALSE, 2),
(16, 5, FALSE, FALSE, 2);

-- Scénario 3: Evening (soirée)
INSERT INTO training_data (hour, day_of_week, presence_detected, light_on, scenario) VALUES
(18, 1, TRUE, TRUE, 3),
(19, 2, TRUE, TRUE, 3),
(20, 3, TRUE, TRUE, 3),
(21, 4, TRUE, TRUE, 3),
(22, 5, TRUE, TRUE, 3);

-- Ajustements Smart Dimming (historique simulation)
INSERT INTO smart_dimming_adjustments (device_id, light_reading_id, scenario, previous_brightness, target_brightness, applied_brightness, reason, adjusted_at) VALUES
(1, 1, 0, 100, 60, 60, 'High natural light detected (350 lux)', NOW() - INTERVAL '1 hour'),
(1, 2, 3, 60, 75, 75, 'Evening scenario activated', NOW() - INTERVAL '30 minutes'),
(7, 3, 0, 80, 50, 50, 'Morning sunlight sufficient (450 lux)', NOW() - INTERVAL '2 hours');

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

COMMENT ON VIEW devices_with_location IS 'Vue simplifiée pour l''affichage dans l''application mobile';

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

COMMENT ON VIEW presence_last_24h IS 'Détections PIR des dernières 24h pour dashboard';

-- Vue: recent_events
-- Affiche les 100 derniers événements avec informations détaillées
CREATE VIEW recent_events AS
SELECT 
    e.id,
    e.timestamp,
    d.name AS device_name,
    r.location,
    e.event_type,
    e.value,
    e.source
FROM events e
LEFT JOIN devices d ON e.device_id = d.id
LEFT JOIN raspberry_pis r ON d.raspberry_pi_id = r.id
ORDER BY e.timestamp DESC
LIMIT 100;

COMMENT ON VIEW recent_events IS 'Historique récent avec contexte complet pour interface web';

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

COMMENT ON VIEW active_rules IS 'Règles actives pour évaluation moteur d''automatisation';

-- Vue: light_readings_hourly_avg
-- Moyenne horaire de luminosité par emplacement (dernières 24h)
CREATE VIEW light_readings_hourly_avg AS
SELECT 
    r.location,
    EXTRACT(HOUR FROM l.measured_at) AS hour,
    ROUND(AVG(l.lux_value)::numeric, 2) AS avg_lux
FROM light_readings l
JOIN raspberry_pis r ON l.raspberry_pi_id = r.id
WHERE l.measured_at >= NOW() - INTERVAL '24 hours'
GROUP BY r.location, EXTRACT(HOUR FROM l.measured_at)
ORDER BY r.location, hour;

COMMENT ON VIEW light_readings_hourly_avg IS 'Tendance luminosité pour graphiques application mobile';

-- Vue: smart_dimming_effectiveness
-- Statistiques d'efficacité du Smart Dimming
CREATE VIEW smart_dimming_effectiveness AS
SELECT 
    d.name AS device_name,
    r.location,
    COUNT(sda.id) AS total_adjustments,
    ROUND(AVG(sda.target_brightness - sda.previous_brightness)::numeric, 2) AS avg_brightness_change,
    ROUND(AVG(ABS(sda.applied_brightness - sda.target_brightness))::numeric, 2) AS avg_deviation,
    MAX(sda.adjusted_at) AS last_adjustment
FROM smart_dimming_adjustments sda
JOIN devices d ON sda.device_id = d.id
JOIN raspberry_pis r ON d.raspberry_pi_id = r.id
GROUP BY d.name, r.location;

COMMENT ON VIEW smart_dimming_effectiveness IS 'KPIs Smart Dimming pour monitoring et amélioration';

-- ============================================================================
-- 6. CRÉATION DES FONCTIONS UTILITAIRES
-- ============================================================================

-- Fonction: get_device_state
-- Retourne l'état actuel d'un appareil avec contexte complet
CREATE OR REPLACE FUNCTION get_device_state(device_id_param INTEGER)
RETURNS TABLE (
    device_name VARCHAR,
    device_type VARCHAR,
    is_on BOOLEAN,
    current_brightness INTEGER,
    location VARCHAR,
    raspberry_pi_online BOOLEAN,
    last_event TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        d.name,
        d.type,
        d.state,
        d.brightness,
        r.location,
        r.is_online,
        MAX(e.timestamp) AS last_event
    FROM devices d
    JOIN raspberry_pis r ON d.raspberry_pi_id = r.id
    LEFT JOIN events e ON e.device_id = d.id
    WHERE d.id = device_id_param
    GROUP BY d.id, d.name, d.type, d.state, d.brightness, r.location, r.is_online;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_device_state(INTEGER) IS 'État complet d''un appareil pour API REST';

-- Fonction: get_presence_count_by_hour
-- Compte le nombre de détections par heure pour une période donnée
CREATE OR REPLACE FUNCTION get_presence_count_by_hour(
    location_param VARCHAR,
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE
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

COMMENT ON FUNCTION get_presence_count_by_hour(VARCHAR, TIMESTAMP WITH TIME ZONE, TIMESTAMP WITH TIME ZONE) IS 'Heatmap de présence pour analyse comportementale';

-- Fonction: calculate_smart_dimming_target
-- Calcule l'intensité cible selon luminosité ambiante et scénario
CREATE OR REPLACE FUNCTION calculate_smart_dimming_target(
    current_lux REAL,
    scenario_param INTEGER
)
RETURNS INTEGER AS $$
DECLARE
    target_brightness INTEGER;
BEGIN
    -- Logique simplifiée (devrait être synchronisée avec l'algorithme backend)
    IF scenario_param = 1 THEN -- Night
        target_brightness := 20;
    ELSIF current_lux < 50 THEN -- Faible luminosité naturelle
        target_brightness := 100;
    ELSIF current_lux BETWEEN 50 AND 200 THEN
        target_brightness := 75;
    ELSIF current_lux BETWEEN 200 AND 500 THEN
        target_brightness := 50;
    ELSE -- Forte luminosité (> 500 lux)
        target_brightness := 25;
    END IF;
    
    RETURN target_brightness;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION calculate_smart_dimming_target(REAL, INTEGER) IS 'Calcul d''intensité idéale (version simplifiée SQL)';

-- Fonction: get_learning_dataset
-- Extrait les données pour apprentissage personnalisé
CREATE OR REPLACE FUNCTION get_learning_dataset(user_id_param INTEGER)
RETURNS TABLE (
    light_level REAL,
    scenario INTEGER,
    time_of_day INTEGER,
    auto_brightness INTEGER,
    manual_brightness INTEGER,
    brightness_diff INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        up.light_level,
        up.scenario,
        up.time_of_day,
        up.auto_brightness,
        up.manual_brightness,
        (up.manual_brightness - up.auto_brightness) AS brightness_diff
    FROM user_preferences up
    WHERE up.user_id = user_id_param
    ORDER BY up.recorded_at DESC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_learning_dataset(INTEGER) IS 'Dataset pour entraînement personnalisé (future régression)';

-- ============================================================================
-- 7. PERMISSIONS ET SÉCURITÉ
-- ============================================================================

-- Créer un utilisateur applicatif avec permissions limitées (optionnel)
-- Décommenter et adapter en production :

-- CREATE USER smarthome_app WITH PASSWORD 'mot_de_passe_fort_genere';
-- GRANT CONNECT ON DATABASE smarthome TO smarthome_app;
-- GRANT USAGE ON SCHEMA public TO smarthome_app;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO smarthome_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO smarthome_app;

-- ============================================================================
-- 8. AFFICHAGE DES STATISTIQUES FINALES
-- ============================================================================

SELECT '[OK] Base de données "smarthome" initialisée avec succès!' AS status;

SELECT 
    'Tables créées' AS category,
    COUNT(*) AS count
FROM information_schema.tables 
WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
UNION ALL
SELECT 
    'Vues créées',
    COUNT(*)
FROM information_schema.views 
WHERE table_schema = 'public'
UNION ALL
SELECT 
    'Fonctions créées',
    COUNT(*)
FROM information_schema.routines 
WHERE routine_schema = 'public'
UNION ALL
SELECT 
    'Index créés',
    COUNT(*)
FROM pg_indexes 
WHERE schemaname = 'public';

-- Statistiques des données insérées
SELECT 
    'Utilisateurs' AS table_name, 
    COUNT(*) AS row_count 
FROM users
UNION ALL
SELECT 'Raspberry Pi', COUNT(*) FROM raspberry_pis
UNION ALL
SELECT 'Appareils', COUNT(*) FROM devices
UNION ALL
SELECT 'Mesures Luminosité', COUNT(*) FROM light_readings
UNION ALL
SELECT 'Détections Présence', COUNT(*) FROM presence
UNION ALL
SELECT 'Règles Actives', COUNT(*) FROM active_rules
UNION ALL
SELECT 'Événements', COUNT(*) FROM events
UNION ALL
SELECT 'Données IA', COUNT(*) FROM training_data
UNION ALL
SELECT 'Ajustements Smart Dimming', COUNT(*) FROM smart_dimming_adjustments;