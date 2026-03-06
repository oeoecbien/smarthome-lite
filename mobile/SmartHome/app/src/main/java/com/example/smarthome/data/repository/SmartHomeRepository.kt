package com.example.smarthome.data.repository

import com.example.smarthome.data.api.UserResponse
import com.example.smarthome.data.model.*

/**
 * Résultat du login : contient le token Bearer ET les infos utilisateur.
 */
data class LoginResult(val token: String, val userInfo: UserResponse)

/**
 * Contrat unique entre le ViewModel et la source de données.
 */
interface SmartHomeRepository {

    suspend fun login(username: String, password: String): LoginResult

    suspend fun forgotPassword(usernameOrEmail: String): String

    suspend fun resetPassword(newPassword: String, token: String): String

    suspend fun getDevices(token: String): List<SmartDevice>

    suspend fun addDevice(token: String, gpioPin: Int, name: String, raspberryPiId: Int, type: String): ApiDevice

    suspend fun deleteDevice(token: String, deviceId: Int)

    suspend fun updateState(token: String, deviceId: Int, state: Boolean, brightness: Int)

    suspend fun updateBrightness(token: String, deviceId: Int, intensity: Float)

    // --- Smart Dimming ---
    suspend fun getSmartDimmingStatus(token: String): SmartDimmingStatus
    suspend fun getSmartDimmingHistory(token: String): List<SmartDimmingAdjustment>
    suspend fun updateSmartDimmingStatus(token: String, enabled: Boolean): SmartDimmingStatus

    // --- Événements ---
    suspend fun getEvents(token: String): List<ApiEvent>

    // --- Inscription ---
    suspend fun register(username: String, email: String, password: String): UserResponse

    // --- Intelligence Artificielle ---
    suspend fun getCurrentScenario(token: String): AIScenarioResponse

    // --- Règles ---
    suspend fun getRules(token: String): List<RuleResponse>
    suspend fun createRule(token: String, rule: RuleRequest): RuleResponse
    suspend fun updateRule(token: String, ruleId: Int, enabled: Boolean): RuleResponse
    suspend fun deleteRule(token: String, ruleId: Int)
}
