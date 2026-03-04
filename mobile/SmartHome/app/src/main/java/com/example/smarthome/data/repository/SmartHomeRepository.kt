package com.example.smarthome.data.repository

import com.example.smarthome.data.api.UserResponse
import com.example.smarthome.data.model.SmartDevice

/**
 * Résultat du login : contient le token Bearer ET les infos utilisateur.
 */
data class LoginResult(val token: String, val userInfo: UserResponse)

/**
 * Contrat unique entre le ViewModel et la source de données.
 * Pour utiliser la vraie API : RepositoryProvider.USE_FAKE = false
 * Pour utiliser les fausses données : RepositoryProvider.USE_FAKE = true
 */
interface SmartHomeRepository {

    /**
     * Authentifie l'utilisateur et retourne le token + ses informations.
     * @throws Exception si les identifiants sont incorrects ou si le réseau est indisponible.
     */
    suspend fun login(username: String, password: String): LoginResult

    /**
     * Récupère la liste complète des appareils (lampes + capteurs).
     */
    suspend fun getDevices(token: String): List<SmartDevice>

    /**
     * Met à jour l'état (on/off) d'un appareil et sa luminosité.
     */
    suspend fun updateState(token: String, deviceId: Int, state: Boolean, brightness: Int)

    /**
     * Met à jour uniquement la luminosité d'un appareil.
     */
    suspend fun updateBrightness(token: String, deviceId: Int, intensity: Float)
}
