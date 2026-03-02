package com.example.smarthome.ui.viewmodel

import com.example.smarthome.data.model.*
import com.example.smarthome.data.api.*

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.isActive


class SmartHomeViewModel : ViewModel() {

    var devices = mutableStateOf<List<SmartDevice>>(emptyList())
        private set

    var errorMessage = mutableStateOf<String?>(null)
        private set

    var isLoading = mutableStateOf(false)
        private set

    var isLoggedIn by mutableStateOf(false)
        private set

    var currentUsername by mutableStateOf("")
        private set

    var currentPassword by mutableStateOf("")
        private set

    // --- CORRECTION ICI : On déclare le token pour qu'il soit accessible partout ---
    private var token: String? = null

    private var debounceJob: Job? = null

    var currentEmail by mutableStateOf("")
        private set

    // Ajoute une variable pour contrôler le polling si besoin
    private var refreshJob: Job? = null

    // Fonction fictive pour simuler l'update (à connecter à l'API plus tard)
    fun updateDevice(device: SmartDevice) {
        // Pour l'instant on ne gère que les lampes
        if (device !is SmartLight) return

        // 1. Mise à jour immédiate de l'écran (pour que ce soit fluide visuellement)
        val currentList = devices.value.toMutableList()
        val index = currentList.indexOfFirst { it.id == device.id }

        if (index == -1) return

        // On sauvegarde l'ancienne version pour pouvoir annuler en cas d'erreur
        val oldDevice = currentList[index]

        // On applique la nouvelle valeur
        currentList[index] = device
        devices.value = currentList

        // 2. Appel API DIRECT (Sans attente, sans délai)
        if (oldDevice is SmartLight) {
            sendUpdateToApi(device, oldDevice)
        }
    }

    private fun sendUpdateToApi(newLamp: SmartLight, oldLamp: SmartLight) {
        viewModelScope.launch {
            try {
                if (token == null) return@launch

                // CAS 1 : C'est l'interrupteur (ON/OFF) qui a changé
                if (newLamp.isOn != oldLamp.isOn) {
                    val brightnessInt = (newLamp.brightness * 100).toInt()
                    val requestBody = DeviceStateRequest(
                        state = newLamp.isOn,
                        brightness = brightnessInt
                    )

                    RetrofitInstance.api.updateState(
                        token = token!!,
                        deviceId = newLamp.id,
                        request = requestBody
                    )
                }

                // CAS 2 : C'est la luminosité qui a changé
                // On vérifie juste si la valeur est différente et si la lampe est allumée
                if (newLamp.brightness != oldLamp.brightness && newLamp.isOn) {
                    RetrofitInstance.api.updateBrightness(
                        token = token!!,
                        deviceId = newLamp.id,
                        intensity = newLamp.brightness
                    )
                }

            } catch (e: Exception) {
                e.printStackTrace()
                // ROLLBACK : En cas d'erreur, on remet l'ancienne valeur
                val currentList = devices.value.toMutableList()
                val idx = currentList.indexOfFirst { it.id == newLamp.id }
                if (idx != -1) {
                    currentList[idx] = oldLamp
                    devices.value = currentList
                }
                errorMessage.value = "Erreur : ${e.localizedMessage}"
            }
        }
    }

    fun login(username: String, password: String) {
        viewModelScope.launch {
            try {
                isLoading.value = true

                // 1. Login & Token
                val tokenResponse = RetrofitInstance.api.login(LoginRequest(username, password))
                token = "Bearer ${tokenResponse.access_token}"

                // 2. Info User
                val userInfo = RetrofitInstance.api.getUserInfo(token!!)
                currentUsername = userInfo.username
                currentEmail = userInfo.email ?: ""



                // 3. Premier chargement des lampes
                fetchDevices()

                isLoggedIn = true

                // --- NOUVEAU : On lance l'actualisation automatique ---
                startAutoRefresh()

            } catch (e: Exception) {
                e.printStackTrace()
                errorMessage.value = "Erreur connexion : ${e.localizedMessage}"
                isLoggedIn = false
            } finally {
                isLoading.value = false
            }
        }
    }

    // J'ai extrait la logique de récupération pour éviter de dupliquer le code
    private suspend fun fetchDevices() {
        if (token == null) return

        val apiDevices = RetrofitInstance.api.getDevices(token!!)

        val deviceList = mutableListOf<SmartDevice>()

        for (device in apiDevices) {
            if (device.type.equals("sensor", ignoreCase = true)) {
                // C'est un capteur -> On récupère ses détails
                try {
                    val sensorData = RetrofitInstance.api.getSensor(token!!, device.id)
                    deviceList.add(
                        SmartSensor(
                            id = device.id,
                            name = device.name,
                            temperature = sensorData.temperature_c ?: 0f,
                            humidity = sensorData.humidity ?: 0,
                            illuminance = sensorData.illuminance_lux ?: 0,
                            motion = sensorData.motion ?: false,
                            battery = sensorData.battery_percent ?: 0
                        )
                    )
                } catch (e: Exception) {
                    e.printStackTrace()
                    // Si erreur capteur, ou peut-être on l'ignore ou on l'ajoute comme simple device inconnu
                }
            } else {
                // C'est une lumière (par défaut)
                deviceList.add(
                    SmartLight(
                        id = device.id,
                        name = device.name,
                        isOn = device.state,
                        brightness = (device.brightness ?: 0) / 100f
                    )
                )
            }
        }

        // On met à jour la liste
        devices.value = deviceList
    }

    private fun startAutoRefresh() {
        // On annule une éventuelle boucle existante pour éviter les doublons
        refreshJob?.cancel()

        refreshJob = viewModelScope.launch {
            // La boucle tourne tant que le ViewModel est actif et qu'on est connecté
            while (isActive && isLoggedIn) {
                delay(3000) // On attend 3 secondes (3000ms)

                // Si l'utilisateur est en train de bouger le slider (debounce actif),
                // on évite de rafraîchir pour ne pas faire "sauter" le slider sous son doigt.
                if (debounceJob?.isActive == true) {
                    continue
                }

                try {
                    if (token != null) {
                        fetchDevices() // On recharge les données
                    }
                } catch (e: Exception) {
                    // En cas d'erreur (ex: coupure réseau temporaire),
                    // on ne fait rien, on réessaiera au prochain tour.
                    e.printStackTrace()
                }
            }
        }
    }

    fun logout() {
        debounceJob?.cancel()
        refreshJob?.cancel()

        // Nettoyage complet
        token = null
        currentUsername = ""
        currentEmail = ""
        devices.value = emptyList()
        errorMessage.value = null

        isLoggedIn = false
    }

}