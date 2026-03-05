package com.example.smarthome.data.repository

import com.example.smarthome.data.api.UserResponse
import com.example.smarthome.data.model.*
import kotlinx.coroutines.delay

/**
 * Implémentation FAKE du repository.
 */
class FakeSmartHomeRepository : SmartHomeRepository {

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

    private val fakeRules = mutableListOf<RuleResponse>()

    override suspend fun login(username: String, password: String): LoginResult {
        delay(600)
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
        throw Exception("Identifiants incorrects")
    }

    override suspend fun getDevices(token: String): List<SmartDevice> {
        delay(400)
        return fakeDevices.toList()
    }

    override suspend fun addDevice(token: String, gpioPin: Int, name: String, raspberryPiId: Int, type: String): ApiDevice {
        delay(500)
        val newId = (fakeDevices.maxOfOrNull { it.id } ?: 0) + 1
        val newDevice = if (type == "sensor") {
            SmartSensor(id = newId, name = name, temperature = 0f, humidity = 0, illuminance = 0, motion = false, battery = 100)
        } else {
            SmartLight(id = newId, name = name, isOn = false, brightness = 0.5f)
        }
        fakeDevices.add(newDevice)
        return ApiDevice(id = newId, name = name, state = false, brightness = 50, type = type)
    }

    override suspend fun updateState(token: String, deviceId: Int, state: Boolean, brightness: Int) {
        delay(200)
        val index = fakeDevices.indexOfFirst { it.id == deviceId }
        if (index != -1) {
            val current = fakeDevices[index]
            if (current is SmartLight) {
                fakeDevices[index] = current.copy(isOn = state, brightness = brightness / 100f)
            }
        }
    }

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

    override suspend fun getSmartDimmingStatus(token: String): SmartDimmingStatus {
        delay(300)
        return SmartDimmingStatus(enabled = false, message = "Désactivé", adjustments_today = 0, active_devices = emptyList())
    }

    override suspend fun getSmartDimmingHistory(token: String): List<SmartDimmingAdjustment> {
        delay(300)
        return emptyList()
    }

    override suspend fun updateSmartDimmingStatus(token: String, enabled: Boolean): SmartDimmingStatus {
        delay(300)
        return SmartDimmingStatus(enabled = enabled, message = "OK", adjustments_today = 0, active_devices = emptyList())
    }

    override suspend fun getEvents(token: String): List<ApiEvent> {
        delay(300)
        return emptyList()
    }

    override suspend fun register(username: String, email: String, password: String): UserResponse {
        delay(600)
        return UserResponse(id = 42, username = username, email = email)
    }

    override suspend fun getCurrentScenario(token: String): AIScenarioResponse {
        delay(500)
        return AIScenarioResponse(
            scenario = 1,
            scenarioName = "Soirée Cinéma",
            confidence = 0.85,
            method = "ML",
            context = AIContext(20, 5, true, true, "pi", emptyList(), emptyList(), 1)
        )
    }

    override suspend fun getRules(token: String): List<RuleResponse> {
        delay(400)
        return fakeRules.toList()
    }

    override suspend fun createRule(token: String, rule: RuleRequest): RuleResponse {
        delay(500)
        val newRule = RuleResponse(
            id = (fakeRules.maxOfOrNull { it.id } ?: 0) + 1,
            name = rule.name,
            description = rule.description,
            enabled = rule.enabled,
            priority = rule.priority,
            condition = rule.condition,
            action = rule.action,
            createdAt = "2026-03-05T12:00:00Z",
            updatedAt = "2026-03-05T12:00:00Z"
        )
        fakeRules.add(newRule)
        return newRule
    }
}
