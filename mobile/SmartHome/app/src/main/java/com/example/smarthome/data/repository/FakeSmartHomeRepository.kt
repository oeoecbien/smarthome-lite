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
}
