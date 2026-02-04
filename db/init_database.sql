-- ============================================================================
-- SmartHome Lite - Script d'Initialisation Base de Données
-- Version sécurisée avec corrections des failles de sécurité
-- Détection de présence via capteur de mouvement MultiSensor7 (Z-Wave)
-- ============================================================================

-- ============================================================================
-- 2. CRÉATION DES TABLES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Table: users
-- Description: Gestion des utilisateurs du système
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE NULL,
    reset_token VARCHAR(255) NULL,
    reset_token_expires TIMESTAMP WITH TIME ZONE NULL,
    CONSTRAINT check_password_hash_length CHECK (LENGTH(password_hash) >= 60),
    CONSTRAINT check_role CHECK (role IN ('user', 'admin'))
);

-- Index pour recherche rapide par username (connexion fréquente)
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username) WHERE deleted_at IS NULL;
-- Index pour recherche par rôle
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role) WHERE deleted_at IS NULL;
-- Index pour soft delete
CREATE INDEX IF NOT EXISTS idx_users_deleted_at ON users(deleted_at) WHERE deleted_at IS NOT NULL;
-- Index pour réinitialisation de mot de passe
CREATE INDEX IF NOT EXISTS idx_users_reset_token ON users(reset_token) WHERE reset_token IS NOT NULL;

COMMENT ON TABLE users IS 'Utilisateurs du système SmartHome';
COMMENT ON COLUMN users.password_hash IS 'Hash bcrypt du mot de passe (12 rounds minimum, 60+ caractères)';
COMMENT ON COLUMN users.username IS 'Nom d''utilisateur unique pour connexion';
COMMENT ON COLUMN users.role IS 'Rôle de l''utilisateur: "user" (par défaut) ou "admin"';
COMMENT ON COLUMN users.deleted_at IS 'Timestamp de suppression (soft delete)';
COMMENT ON COLUMN users.reset_token IS 'Token de réinitialisation de mot de passe (généré avec secrets.token_urlsafe)';
COMMENT ON COLUMN users.reset_token_expires IS 'Date d''expiration du token de réinitialisation (généralement 1 heure après génération)';

-- ----------------------------------------------------------------------------
-- Table: raspberry_pis
-- Description: Configuration des Raspberry Pi dans le réseau
-- SÉCURITÉ: API keys hashées avec bcrypt
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raspberry_pis (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    location VARCHAR(100) NOT NULL,
    ip_address VARCHAR(15),
    api_key_hash VARCHAR(255) NOT NULL UNIQUE,
    is_online BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE NULL,
    CONSTRAINT check_ip_format CHECK (ip_address IS NULL OR ip_address ~ '^([0-9]{1,3}\.){3}[0-9]{1,3}$'),
    CONSTRAINT check_api_key_hash_length CHECK (LENGTH(api_key_hash) >= 60)
);

-- Index pour recherche par localisation et état
CREATE INDEX IF NOT EXISTS idx_raspberry_pis_location ON raspberry_pis(location) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_raspberry_pis_online ON raspberry_pis(is_online) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_raspberry_pis_deleted_at ON raspberry_pis(deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE raspberry_pis IS 'Raspberry Pi déployés dans l''habitat';
COMMENT ON COLUMN raspberry_pis.api_key_hash IS 'Hash bcrypt de la clé API (12 rounds minimum, jamais stockée en clair)';
COMMENT ON COLUMN raspberry_pis.is_online IS 'État de connexion (heartbeat toutes les 30s)';
COMMENT ON COLUMN raspberry_pis.deleted_at IS 'Timestamp de suppression (soft delete)';

-- ----------------------------------------------------------------------------
-- Table: devices
-- Description: Appareils connectés (lampes, prises, etc.)
-- SÉCURITÉ: ON DELETE RESTRICT pour éviter perte de données
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS devices (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    raspberry_pi_id INTEGER NOT NULL REFERENCES raspberry_pis(id) ON DELETE RESTRICT,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(20) NOT NULL,
    state BOOLEAN DEFAULT FALSE NOT NULL,
    brightness INTEGER DEFAULT 0 NOT NULL,
    gpio_pin INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE NULL,
    CONSTRAINT check_device_type CHECK (type IN ('light', 'dimmer', 'socket')),
    CONSTRAINT check_gpio_pin_range CHECK (gpio_pin >= 1 AND gpio_pin <= 40),
    CONSTRAINT check_brightness_range CHECK (brightness >= 0 AND brightness <= 100),
    CONSTRAINT uq_device_raspberry_pi_gpio UNIQUE(raspberry_pi_id, gpio_pin)
);

-- Index pour requêtes fréquentes (liste par emplacement, par type)
CREATE INDEX IF NOT EXISTS idx_devices_user_id ON devices(user_id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_devices_raspberry_pi ON devices(raspberry_pi_id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_devices_type ON devices(type) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_devices_state ON devices(state) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_devices_deleted_at ON devices(deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE devices IS 'Appareils électriques contrôlables';
COMMENT ON COLUMN devices.user_id IS 'Propriétaire de l''appareil (relation avec users)';
COMMENT ON COLUMN devices.gpio_pin IS 'Pin GPIO physique sur le Raspberry Pi (unique par RPi)';
COMMENT ON COLUMN devices.brightness IS 'Intensité lumineuse pour les dimmers (0-100)';
COMMENT ON COLUMN devices.deleted_at IS 'Timestamp de suppression (soft delete)';

-- ----------------------------------------------------------------------------
-- Table: light_readings
-- Description: Mesures de luminosité ambiante
-- OPTIMISATION: Préparé pour partitionnement par date
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS light_readings (
    id SERIAL PRIMARY KEY,
    raspberry_pi_id INTEGER NOT NULL REFERENCES raspberry_pis(id) ON DELETE RESTRICT,
    lux_value REAL NOT NULL,
    sensor_type VARCHAR(20) NOT NULL DEFAULT 'BH1750',
    measured_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_lux_value_range CHECK (lux_value >= 0),
    CONSTRAINT check_sensor_type CHECK (sensor_type IN ('BH1750', 'LDR'))
);

-- Index pour requêtes temporelles (graphiques, tendances)
CREATE INDEX IF NOT EXISTS idx_light_readings_measured_at ON light_readings(measured_at DESC);
CREATE INDEX IF NOT EXISTS idx_light_readings_raspberry_pi ON light_readings(raspberry_pi_id);
-- Index composite pour requêtes fréquentes
CREATE INDEX IF NOT EXISTS idx_light_readings_rpi_measured ON light_readings(raspberry_pi_id, measured_at DESC);

COMMENT ON TABLE light_readings IS 'Historique des mesures de luminosité ambiante';
COMMENT ON COLUMN light_readings.lux_value IS 'Intensité lumineuse en lux (0-65535 pour BH1750)';

-- ----------------------------------------------------------------------------
-- Table: presence
-- Description: Historique des détections de présence via capteur de mouvement (MultiSensor7 Z-Wave)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS presence (
    id SERIAL PRIMARY KEY,
    raspberry_pi_id INTEGER NOT NULL REFERENCES raspberry_pis(id) ON DELETE RESTRICT,
    detected_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sensor_node_id INTEGER NULL
);

-- Index pour recherche par date et par Raspberry Pi
CREATE INDEX IF NOT EXISTS idx_presence_detected_at ON presence(detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_presence_raspberry_pi ON presence(raspberry_pi_id);
CREATE INDEX IF NOT EXISTS idx_presence_rpi_detected ON presence(raspberry_pi_id, detected_at DESC);

COMMENT ON TABLE presence IS 'Journal des détections de mouvement (MultiSensor7 Z-Wave)';
COMMENT ON COLUMN presence.sensor_node_id IS 'Node ID Z-Wave du capteur de mouvement (ex: MultiSensor7)';

-- ----------------------------------------------------------------------------
-- Table: rules
-- Description: Règles d'automatisation définies par l'utilisateur
-- SÉCURITÉ: Ajout user_id pour isolation
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS rules (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    enabled BOOLEAN DEFAULT TRUE NOT NULL,
    condition JSONB NOT NULL,
    action JSONB NOT NULL,
    priority INTEGER DEFAULT 5 NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE NULL,
    CONSTRAINT check_priority_range CHECK (priority >= 1 AND priority <= 10)
);

-- Index pour recherche des règles actives et tri par priorité
CREATE INDEX IF NOT EXISTS idx_rules_user_id ON rules(user_id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_rules_enabled ON rules(enabled) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_rules_priority ON rules(priority DESC) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_rules_deleted_at ON rules(deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE rules IS 'Règles d''automatisation (format JSON pour flexibilité)';
COMMENT ON COLUMN rules.user_id IS 'Propriétaire de la règle';
COMMENT ON COLUMN rules.condition IS 'Conditions d''activation (JSON: type, value, operators)';
COMMENT ON COLUMN rules.action IS 'Action à exécuter (JSON: type, device_id, parameters)';
COMMENT ON COLUMN rules.priority IS '1=basse, 10=haute (ordre d''évaluation)';
COMMENT ON COLUMN rules.deleted_at IS 'Timestamp de suppression (soft delete)';

-- ----------------------------------------------------------------------------
-- Table: events
-- Description: Journal des événements système (actions, changements d'état)
-- OPTIMISATION: Index composite pour requêtes fréquentes
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    device_id INTEGER REFERENCES devices(id) ON DELETE SET NULL,
    event_type VARCHAR(50) NOT NULL,
    value VARCHAR(100),
    source VARCHAR(20),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_event_source CHECK (source IS NULL OR source IN ('manual', 'automatic', 'ai', 'system', 'smart_dimming'))
);

-- Index pour recherche par device, type et date
CREATE INDEX IF NOT EXISTS idx_events_device_id ON events(device_id);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_source ON events(source);
CREATE INDEX IF NOT EXISTS idx_events_event_type ON events(event_type);
-- Index composite pour requêtes fréquentes
CREATE INDEX IF NOT EXISTS idx_events_device_timestamp ON events(device_id, timestamp DESC) WHERE device_id IS NOT NULL;

COMMENT ON TABLE events IS 'Audit trail de toutes les actions système';
COMMENT ON COLUMN events.source IS 'Origine de l''événement (ajout "smart_dimming")';

-- ----------------------------------------------------------------------------
-- Table: training_data
-- Description: Données d'entraînement pour l'algorithme de classification IA
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS training_data (
    id SERIAL PRIMARY KEY,
    hour INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    presence_detected BOOLEAN NOT NULL,
    light_on BOOLEAN NOT NULL,
    scenario INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_training_hour_range CHECK (hour >= 0 AND hour <= 23),
    CONSTRAINT check_training_day_of_week_range CHECK (day_of_week >= 0 AND day_of_week <= 6),
    CONSTRAINT check_training_scenario_range CHECK (scenario >= 0 AND scenario <= 3)
);

-- Index pour analyse de données
CREATE INDEX IF NOT EXISTS idx_training_data_scenario ON training_data(scenario);
CREATE INDEX IF NOT EXISTS idx_training_data_hour ON training_data(hour);

COMMENT ON TABLE training_data IS 'Dataset pour entraînement Decision Tree (4 scénarios)';
COMMENT ON COLUMN training_data.scenario IS '0=Day, 1=Night, 2=Away, 3=Evening';

-- ----------------------------------------------------------------------------
-- Table: smart_dimming_adjustments
-- Description: Historique des ajustements automatiques d'intensité
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS smart_dimming_adjustments (
    id SERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE RESTRICT,
    light_reading_id INTEGER REFERENCES light_readings(id) ON DELETE SET NULL,
    scenario INTEGER NOT NULL,
    previous_brightness INTEGER NOT NULL,
    target_brightness INTEGER NOT NULL,
    applied_brightness INTEGER NOT NULL,
    reason VARCHAR(200),
    adjusted_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_dimming_scenario_range CHECK (scenario >= 0 AND scenario <= 3),
    CONSTRAINT check_previous_brightness_range CHECK (previous_brightness >= 0 AND previous_brightness <= 100),
    CONSTRAINT check_target_brightness_range CHECK (target_brightness >= 0 AND target_brightness <= 100),
    CONSTRAINT check_applied_brightness_range CHECK (applied_brightness >= 0 AND applied_brightness <= 100)
);

-- Index pour analyse des ajustements
CREATE INDEX IF NOT EXISTS idx_dimming_device ON smart_dimming_adjustments(device_id);
CREATE INDEX IF NOT EXISTS idx_dimming_adjusted_at ON smart_dimming_adjustments(adjusted_at DESC);
CREATE INDEX IF NOT EXISTS idx_dimming_scenario ON smart_dimming_adjustments(scenario);

COMMENT ON TABLE smart_dimming_adjustments IS 'Enregistre chaque ajustement automatique pour analyse';
COMMENT ON COLUMN smart_dimming_adjustments.reason IS 'Justification textuelle (ex: "High natural light")';
COMMENT ON COLUMN smart_dimming_adjustments.target_brightness IS 'Intensité calculée par l''algorithme';
COMMENT ON COLUMN smart_dimming_adjustments.applied_brightness IS 'Intensité réellement appliquée (peut différer)';

-- ----------------------------------------------------------------------------
-- Table: user_preferences
-- Description: Apprentissage des préférences utilisateur
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE RESTRICT,
    light_level REAL NOT NULL,
    scenario INTEGER NOT NULL,
    auto_brightness INTEGER NOT NULL,
    manual_brightness INTEGER NOT NULL,
    time_of_day INTEGER NOT NULL,
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_pref_light_level_range CHECK (light_level >= 0),
    CONSTRAINT check_pref_scenario_range CHECK (scenario >= 0 AND scenario <= 3),
    CONSTRAINT check_pref_auto_brightness_range CHECK (auto_brightness >= 0 AND auto_brightness <= 100),
    CONSTRAINT check_pref_manual_brightness_range CHECK (manual_brightness >= 0 AND manual_brightness <= 100),
    CONSTRAINT check_pref_time_of_day_range CHECK (time_of_day >= 0 AND time_of_day <= 23)
);

-- Index pour analyse des préférences
CREATE INDEX IF NOT EXISTS idx_preferences_user ON user_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_preferences_device ON user_preferences(device_id);
CREATE INDEX IF NOT EXISTS idx_preferences_scenario ON user_preferences(scenario);

COMMENT ON TABLE user_preferences IS 'Capture les ajustements manuels pour apprentissage personnalisé';
COMMENT ON COLUMN user_preferences.auto_brightness IS 'Intensité proposée par le système';
COMMENT ON COLUMN user_preferences.manual_brightness IS 'Intensité choisie par l''utilisateur (feedback)';

-- ----------------------------------------------------------------------------
-- Table: audit_log
-- Description: Journal d'audit pour traçabilité des modifications sensibles
-- NOUVEAU: Table d'audit pour sécurité
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action_type VARCHAR(50) NOT NULL,
    table_name VARCHAR(50) NOT NULL,
    record_id INTEGER,
    old_values JSONB,
    new_values JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_action_type CHECK (action_type IN ('INSERT', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT', 'FAILED_LOGIN'))
);

-- Index pour recherche d'audit
CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_table_name ON audit_log(table_name);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_action_type ON audit_log(action_type);

COMMENT ON TABLE audit_log IS 'Journal d''audit pour traçabilité des actions sensibles';
COMMENT ON COLUMN audit_log.action_type IS 'Type d''action: INSERT, UPDATE, DELETE, LOGIN, LOGOUT, FAILED_LOGIN';
COMMENT ON COLUMN audit_log.old_values IS 'Valeurs avant modification (JSON)';
COMMENT ON COLUMN audit_log.new_values IS 'Valeurs après modification (JSON)';

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

-- Fonction pour journaliser les modifications dans audit_log
CREATE OR REPLACE FUNCTION log_audit_event()
RETURNS TRIGGER AS $$
DECLARE
    v_user_id INTEGER;
    v_action VARCHAR(50);
    v_old_values JSONB;
    v_new_values JSONB;
BEGIN
    -- Déterminer l'action
    IF TG_OP = 'INSERT' THEN
        v_action := 'INSERT';
        v_new_values := to_jsonb(NEW);
        v_old_values := NULL;
    ELSIF TG_OP = 'UPDATE' THEN
        v_action := 'UPDATE';
        v_old_values := to_jsonb(OLD);
        v_new_values := to_jsonb(NEW);
    ELSIF TG_OP = 'DELETE' THEN
        v_action := 'DELETE';
        v_old_values := to_jsonb(OLD);
        v_new_values := NULL;
    END IF;
    
    -- Tables sensibles à auditer
    IF TG_TABLE_NAME IN ('users', 'raspberry_pis', 'devices', 'rules') THEN
        -- Récupérer user_id depuis la session si disponible (via current_setting)
        -- Note: Le backend doit définir current_setting('app.user_id') avant les opérations
        BEGIN
            v_user_id := current_setting('app.user_id', true)::INTEGER;
        EXCEPTION WHEN OTHERS THEN
            v_user_id := NULL;
        END;
        
        INSERT INTO audit_log (
            user_id,
            action_type,
            table_name,
            record_id,
            old_values,
            new_values
        ) VALUES (
            v_user_id,
            v_action,
            TG_TABLE_NAME,
            COALESCE(NEW.id, OLD.id),
            v_old_values,
            v_new_values
        );
    END IF;
    
    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION log_audit_event() IS 'Trigger pour journaliser les modifications dans audit_log';

-- Appliquer le trigger sur les tables avec updated_at
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_raspberry_pis_updated_at ON raspberry_pis;
CREATE TRIGGER update_raspberry_pis_updated_at BEFORE UPDATE ON raspberry_pis
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_devices_updated_at ON devices;
CREATE TRIGGER update_devices_updated_at BEFORE UPDATE ON devices
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_rules_updated_at ON rules;
CREATE TRIGGER update_rules_updated_at BEFORE UPDATE ON rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Appliquer les triggers d'audit sur les tables sensibles
DROP TRIGGER IF EXISTS audit_users ON users;
CREATE TRIGGER audit_users AFTER INSERT OR UPDATE OR DELETE ON users
    FOR EACH ROW EXECUTE FUNCTION log_audit_event();

DROP TRIGGER IF EXISTS audit_raspberry_pis ON raspberry_pis;
CREATE TRIGGER audit_raspberry_pis AFTER INSERT OR UPDATE OR DELETE ON raspberry_pis
    FOR EACH ROW EXECUTE FUNCTION log_audit_event();

DROP TRIGGER IF EXISTS audit_devices ON devices;
CREATE TRIGGER audit_devices AFTER INSERT OR UPDATE OR DELETE ON devices
    FOR EACH ROW EXECUTE FUNCTION log_audit_event();

DROP TRIGGER IF EXISTS audit_rules ON rules;
CREATE TRIGGER audit_rules AFTER INSERT OR UPDATE OR DELETE ON rules
    FOR EACH ROW EXECUTE FUNCTION log_audit_event();

-- ============================================================================
-- 4. INSERTION DES DONNÉES DE TEST
-- ============================================================================

-- NOTE: Les données de test ont été supprimées.
-- L'utilisateur admin et les données de test doivent être créés via le backend.
-- 
-- Pour créer l'utilisateur admin :
-- 1. Démarrer le backend : uvicorn app.main:app --reload
-- 2. Utiliser la route temporaire /api/auth/create-admin (si disponible)
--    ou créer manuellement via l'interface d'administration
--
-- La base de données est initialisée vide, prête à recevoir les données via l'API.

-- ============================================================================
-- 5. CRÉATION DES VUES UTILES
-- ============================================================================

-- Vue: devices_with_location
-- Affiche les appareils avec leur localisation (via Raspberry Pi)
CREATE OR REPLACE VIEW devices_with_location AS
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
JOIN raspberry_pis r ON d.raspberry_pi_id = r.id
WHERE d.deleted_at IS NULL AND r.deleted_at IS NULL;

COMMENT ON VIEW devices_with_location IS 'Vue simplifiée pour l''affichage dans l''application mobile';

-- Vue: presence_last_24h
-- Affiche les détections de mouvement (MultiSensor7) des dernières 24 heures
CREATE OR REPLACE VIEW presence_last_24h AS
SELECT 
    p.id,
    p.detected_at,
    r.name AS raspberry_pi_name,
    r.location,
    p.sensor_node_id
FROM presence p
JOIN raspberry_pis r ON p.raspberry_pi_id = r.id
WHERE p.detected_at >= NOW() - INTERVAL '24 hours'
  AND r.deleted_at IS NULL
ORDER BY p.detected_at DESC;

COMMENT ON VIEW presence_last_24h IS 'Détections de mouvement (MultiSensor7) des dernières 24h pour dashboard';

-- Vue: recent_events
-- Affiche les 100 derniers événements avec informations détaillées
CREATE OR REPLACE VIEW recent_events AS
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
WHERE d.deleted_at IS NULL OR d.deleted_at IS NULL
ORDER BY e.timestamp DESC
LIMIT 100;

COMMENT ON VIEW recent_events IS 'Historique récent avec contexte complet pour interface web';

-- Vue: active_rules
-- Affiche uniquement les règles actives triées par priorité
CREATE OR REPLACE VIEW active_rules AS
SELECT 
    id,
    user_id,
    name,
    description,
    condition,
    action,
    priority
FROM rules
WHERE enabled = TRUE AND deleted_at IS NULL
ORDER BY priority DESC;

COMMENT ON VIEW active_rules IS 'Règles actives pour évaluation moteur d''automatisation';

-- Vue: light_readings_hourly_avg
-- Moyenne horaire de luminosité par emplacement (dernières 24h)
CREATE OR REPLACE VIEW light_readings_hourly_avg AS
SELECT 
    r.location,
    EXTRACT(HOUR FROM l.measured_at) AS hour,
    ROUND(AVG(l.lux_value)::numeric, 2) AS avg_lux
FROM light_readings l
JOIN raspberry_pis r ON l.raspberry_pi_id = r.id
WHERE l.measured_at >= NOW() - INTERVAL '24 hours'
  AND r.deleted_at IS NULL
GROUP BY r.location, EXTRACT(HOUR FROM l.measured_at)
ORDER BY r.location, hour;

COMMENT ON VIEW light_readings_hourly_avg IS 'Tendance luminosité pour graphiques application mobile';

-- Vue: smart_dimming_effectiveness
-- Statistiques d'efficacité du Smart Dimming
CREATE OR REPLACE VIEW smart_dimming_effectiveness AS
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
WHERE d.deleted_at IS NULL AND r.deleted_at IS NULL
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
      AND d.deleted_at IS NULL
      AND r.deleted_at IS NULL
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
        AND r.deleted_at IS NULL
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

-- Créer un utilisateur applicatif avec permissions limitées (recommandé en production)
-- Décommenter et adapter selon vos besoins :

-- CREATE USER smarthome_app WITH PASSWORD 'mot_de_passe_fort_genere';
-- GRANT CONNECT ON DATABASE smarthome TO smarthome_app;
-- GRANT USAGE ON SCHEMA public TO smarthome_app;
-- 
-- -- Permissions en lecture seule pour analytics
-- CREATE ROLE smarthome_readonly;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO smarthome_readonly;
-- GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO smarthome_readonly;
-- GRANT smarthome_readonly TO smarthome_app;
-- 
-- -- Permissions en écriture pour l'API (sans accès direct aux mots de passe)
-- CREATE ROLE smarthome_api;
-- GRANT SELECT, INSERT, UPDATE ON devices, events, presence, light_readings, 
--     smart_dimming_adjustments, user_preferences, training_data TO smarthome_api;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON rules TO smarthome_api;
-- -- Accès limité à users (pas de SELECT sur password_hash)
-- GRANT SELECT (id, username, email, role, created_at, updated_at) ON users TO smarthome_api;
-- GRANT INSERT, UPDATE (username, email, role) ON users TO smarthome_api;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO smarthome_api;
-- GRANT smarthome_api TO smarthome_app;

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

-- Statistiques des tables créées (base vide)
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
SELECT 'Règles', COUNT(*) FROM rules
UNION ALL
SELECT 'Événements', COUNT(*) FROM events
UNION ALL
SELECT 'Données IA', COUNT(*) FROM training_data
UNION ALL
SELECT 'Ajustements Smart Dimming', COUNT(*) FROM smart_dimming_adjustments
UNION ALL
SELECT 'Audit Log', COUNT(*) FROM audit_log;
