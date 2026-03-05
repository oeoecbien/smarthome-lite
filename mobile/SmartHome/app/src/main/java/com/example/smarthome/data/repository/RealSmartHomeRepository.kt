package com.example.smarthome.data.repository

import com.example.smarthome.data.api.DeviceStateRequest
import com.example.smarthome.data.api.RetrofitInstance
import com.example.smarthome.data.api.UserResponse
import com.example.smarthome.data.model.*
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope

/**
 * Implémentation RÉELLE du repository.
 * Délègue tous les appels à l'API via Retrofit.
 */
class RealSmartHomeRepository : SmartHomeRepository {

    private val api = RetrofitInstance.api

    override suspend fun login(username: String, password: String): LoginResult {
        val loginRequest = com.example.smarthome.data.model.LoginRequest(username, password)
        val tokenResponse = api.login(loginRequest)
        val bearerToken = "Bearer ${tokenResponse.access_token}"
        val userInfo = api.getUserInfo(bearerToken)
        return LoginResult(token = bearerToken, userInfo = userInfo)
    }

    override suspend fun getDevices(token: String): List<SmartDevice> = coroutineScope {
        val apiDevices = api.getDevices(token)
        
        // On lance la récupération des détails de chaque device en parallèle
        apiDevices.map { device ->
            async {
                if (device.type.equals("sensor", ignoreCase = true)) {
                    try {
                        val sensorData = api.getSensor(token, device.id)
                        SmartSensor(
                            id          = device.id,
                            name        = device.name,
                            temperature = sensorData.temperature_c ?: 0f,
                            humidity    = sensorData.humidity ?: 0,
                            illuminance = sensorData.illuminance_lux ?: 0,
                            motion      = sensorData.motion ?: false,
                            battery     = sensorData.battery_percent ?: 0
                        )
                    } catch (e: Exception) {
                        e.printStackTrace()
                        null // Si un capteur échoue, on l'ignore proprement
                    }
                } else {
                    SmartLight(
                        id         = device.id,
                        name       = device.name,
                        isOn       = device.state,
                        brightness = (device.brightness ?: 0) / 100f
                    )
                }
            }
        }.awaitAll().filterNotNull()
    }

    override suspend fun addDevice(token: String, gpioPin: Int, name: String, raspberryPiId: Int, type: String): ApiDevice {
        val request = AddDeviceRequest(gpio_pin = gpioPin, name = name, raspberry_pi_id = raspberryPiId, type = type)
        return api.addDevice(token, request)
    }

    override suspend fun updateState(
        token: String, deviceId: Int, state: Boolean, brightness: Int
    ) {
        api.updateState(token, deviceId, DeviceStateRequest(state, brightness))
    }

    override suspend fun updateBrightness(token: String, deviceId: Int, intensity: Float) {
        api.updateBrightness(token, deviceId, intensity)
    }

    override suspend fun getSmartDimmingStatus(token: String): com.example.smarthome.data.model.SmartDimmingStatus {
        return api.getSmartDimmingStatus(token)
    }

    override suspend fun getSmartDimmingHistory(token: String): List<com.example.smarthome.data.model.SmartDimmingAdjustment> {
        return api.getSmartDimmingHistory(token)
    }

    override suspend fun updateSmartDimmingStatus(token: String, enabled: Boolean): com.example.smarthome.data.model.SmartDimmingStatus {
        val request = com.example.smarthome.data.model.SmartDimmingRequest(enabled = enabled)
        return api.updateSmartDimmingStatus(token, request)
    }

    override suspend fun getEvents(token: String): List<com.example.smarthome.data.model.ApiEvent> {
        return api.getEvents(token)
    }

    override suspend fun register(username: String, email: String, password: String): UserResponse {
        val request = com.example.smarthome.data.model.RegisterRequest(username, email, password)
        return api.register(request)
    }

    override suspend fun getCurrentScenario(token: String): AIScenarioResponse {
        return api.getAICurrentScenario(token)
    }
}
