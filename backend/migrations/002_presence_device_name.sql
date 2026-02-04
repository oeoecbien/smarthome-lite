-- Ajout du nom BLE (annoncé par l'appareil) aux détections de présence.
ALTER TABLE presence ADD COLUMN IF NOT EXISTS device_name VARCHAR(100);
COMMENT ON COLUMN presence.device_name IS 'Nom BLE annoncé par l''appareil (ex: Galaxy A52, iPhone)';
