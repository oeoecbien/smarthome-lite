package com.example.smarthome.data.repository

import com.example.smarthome.data.api.UserResponse
import com.example.smarthome.data.model.SmartDevice
import com.example.smarthome.data.model.SmartLight
import com.example.smarthome.data.model.SmartSensor
import kotlinx.coroutines.delay

/**
 * Implémentation FAKE du repository.
 * Retourne des données codées en dur avec un délai pour simuler le réseau.
 *
 * Identifiants valides : admin / admin
 */
class FakeSmartHomeRepository : SmartHomeRepository {

    // ─── Données fake persistantes (mutable pour simuler les mises à jour) ───────
    private val fakeDevices: MutableList<SmartDevice> = mutableListOf(
        SmartLight(id = 1, name = "Lampe Salon",   isOn = true,  brightness = 0.75f),
        SmartLight(id = 2, name = "Lampe Chambre", isOn = false, brightness = 0.50f),
        SmartLight(id = 3, name = "Lampe Cuisine", isOn = true,  brightness = 1.00f),
        SmartSensor(
            id          = 4,
            name        = "Capteur Entrée",
            temperature = 21.5f,
            humidity    = 55,
            illuminance = 342,
            motion      = false,
            battery     = 87
        )
    )

    // ─── Login ────────────────────────────────────────────────────────────────────
    override suspend fun login(username: String, password: String): LoginResult {
        delay(600) // Simule la latence réseau

        if (username == "admin" && password == "admin") {
            return LoginResult(
                token = "Bearer fake-token",
                userInfo = UserResponse(
                    id        = 1,
                    username  = "admin",
                    email     = "admin@smarthome.local",
                    full_name = "Administrateur"
                )
            )
        }
        // Simule une erreur HTTP 401
        throw Exception("Identifiants incorrects (utilisez admin / admin en mode fake)")
    }

    // ─── Devices ──────────────────────────────────────────────────────────────────
    override suspend fun getDevices(token: String): List<SmartDevice> {
        delay(400)
        return fakeDevices.toList() // Copie défensive
    }

    // ─── updateState ──────────────────────────────────────────────────────────────
    override suspend fun updateState(
        token: String, deviceId: Int, state: Boolean, brightness: Int
    ) {
        delay(200)
        val index = fakeDevices.indexOfFirst { it.id == deviceId }
        if (index != -1) {
            val current = fakeDevices[index]
            if (current is SmartLight) {
                fakeDevices[index] = current.copy(
                    isOn       = state,
                    brightness = brightness / 100f
                )
            }
        }
    }

    // ─── updateBrightness ─────────────────────────────────────────────────────────
    override suspend fun updateBrightness(token: String, deviceId: Int, intensity: Float) {
        delay(200)
        val index = fakeDevices.indexOfFirst { it.id == deviceId }
        if (index != -1) {
            val current = fakeDevices[index]
            if (current is SmartLight) {
                fakeDevices[index] = current.copy(brightness = intensity)
            }
        }
    }

    // ─── Smart Dimming (Fake) ─────────────────────────────────────────────────────
    private var fakeSmartDimmingEnabled = false

    override suspend fun getSmartDimmingStatus(token: String): com.example.smarthome.data.model.SmartDimmingStatus {
        delay(300)
        return com.example.smarthome.data.model.SmartDimmingStatus(
            enabled = fakeSmartDimmingEnabled,
            adjustments_today = 12,
            active_devices = listOf(1, 2)
        )
    }

    override suspend fun getSmartDimmingHistory(token: String): List<com.example.smarthome.data.model.SmartDimmingAdjustment> {
        delay(400)
        return listOf(
            com.example.smarthome.data.model.SmartDimmingAdjustment(
                id = 101,
                device_id = 1,
                device_name = "Lampe Salon",
                scenario = 0,
                brightness_before = 20,
                brightness_after = 45,
                reason = "ML prediction",
                timestamp = "2026-03-04T10:15:00Z"
            ),
            com.example.smarthome.data.model.SmartDimmingAdjustment(
                id = 102,
                device_id = 2,
                device_name = "Lampe Chambre",
                scenario = 0,
                brightness_before = 80,
                brightness_after = 30,
                reason = "Time of day",
                timestamp = "2026-03-04T09:30:00Z"
            )
        )
    }

    override suspend fun updateSmartDimmingStatus(token: String, enabled: Boolean): com.example.smarthome.data.model.SmartDimmingStatus {
        delay(300)
        fakeSmartDimmingEnabled = enabled
        return com.example.smarthome.data.model.SmartDimmingStatus(
            enabled = enabled,
            adjustments_today = 12,
            active_devices = listOf(1, 2)
        )
    }
}
