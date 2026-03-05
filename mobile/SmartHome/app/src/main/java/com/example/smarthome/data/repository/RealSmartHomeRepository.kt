package com.example.smarthome.data.repository

import com.example.smarthome.data.api.DeviceStateRequest
import com.example.smarthome.data.api.RetrofitInstance
import com.example.smarthome.data.api.UserResponse
import com.example.smarthome.data.model.SmartDevice
import com.example.smarthome.data.model.SmartLight
import com.example.smarthome.data.model.SmartSensor

/**
 * Implémentation RÉELLE du repository.
 * Délègue tous les appels à l'API via Retrofit.
 * Utiliser cette implémentation quand l'API est de nouveau accessible.
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

    override suspend fun getDevices(token: String): List<SmartDevice> {
        val apiDevices = api.getDevices(token)
        val deviceList = mutableListOf<SmartDevice>()

        for (device in apiDevices) {
            if (device.type.equals("sensor", ignoreCase = true)) {
                try {
                    val sensorData = api.getSensor(token, device.id)
                    deviceList.add(
                        SmartSensor(
                            id          = device.id,
                            name        = device.name,
                            temperature = sensorData.temperature_c ?: 0f,
                            humidity    = sensorData.humidity ?: 0,
                            illuminance = sensorData.illuminance_lux ?: 0,
                            motion      = sensorData.motion ?: false,
                            battery     = sensorData.battery_percent ?: 0
                        )
                    )
                } catch (e: Exception) {
                    e.printStackTrace()
                }
            } else {
                deviceList.add(
                    SmartLight(
                        id         = device.id,
                        name       = device.name,
                        isOn       = device.state,
                        brightness = (device.brightness ?: 0) / 100f
                    )
                )
            }
        }
        return deviceList
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
}
