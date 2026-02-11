package com.example.smarthome

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.compose.viewModel
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.time.delay


class SmartHomeViewModel : ViewModel() {

    var lamps = mutableStateOf<List<SmartLamp>>(emptyList())
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


    fun loadData(username: String, password: String) {
        viewModelScope.launch {
            try {
                errorMessage.value = null

                val tokenResponse = RetrofitInstance.api.login(LoginRequest(username, password))

                val bearerToken = "Bearer ${tokenResponse.access_token}"

                val apiDevices = RetrofitInstance.api.getDevices(bearerToken)

                lamps.value = apiDevices.map { device ->
                    SmartLamp(
                        id = device.id,
                        name = device.name,
                        isOn = device.is_active,
                        brightness = device.intensity ?: 0.5f
                    )
                }

            } catch (e: Exception) {
                e.printStackTrace()
                errorMessage.value = "Erreur: ${e.message}"
            }


        }
    }

    // Fonction fictive pour simuler l'update (à connecter à l'API plus tard)
    fun updateLamp(lamp: SmartLamp) {
        // 1. Optimiste UI Update
        val currentList = lamps.value.toMutableList()
        val index = currentList.indexOfFirst { it.id == lamp.id }

        if (index == -1) return

        val oldLamp = currentList[index]
        currentList[index] = lamp
        lamps.value = currentList


        // 2. Logique Debounce
        if (oldLamp.isOn != lamp.isOn) {
            sendUpdateToApi(lamp, oldLamp)
            return
        }

        if (oldLamp.brightness != lamp.brightness) {
            debounceJob?.cancel()
            debounceJob = viewModelScope.launch {
                delay(500)
                sendUpdateToApi(lamp, oldLamp)
            }
        }
    }

    // --- 3. FONCTION PRIVÉE POUR L'APPEL API ---
    // J'ai isolé l'appel API pour ne pas dupliquer le code
    private fun sendUpdateToApi(newLamp: SmartLamp, oldLamp: SmartLamp) {
        viewModelScope.launch {
            try {
                // Vérification que le token existe
                if (token == null) return@launch

                // Appel API
                // Ici token!! fonctionne car on a vérifié qu'il n'est pas null juste avant
                RetrofitInstance.api.updateBrightness(
                    token = token!!,
                    deviceId = newLamp.id,
                    intensity = newLamp.brightness
                )

            } catch (e: Exception) {
                e.printStackTrace()
                // Rollback en cas d'erreur
                val currentList = lamps.value.toMutableList()
                val idx = currentList.indexOfFirst { it.id == newLamp.id }
                if (idx != -1) {
                    currentList[idx] = oldLamp
                    lamps.value = currentList
                }
                errorMessage.value = "Erreur synchro : ${e.localizedMessage}"
            }
        }
    }

    fun login(username: String, password: String) {
        viewModelScope.launch {
            try {
                isLoading.value = true
                errorMessage.value = null

                // 1. Connexion (POST /api/auth/login)
                val tokenResponse = RetrofitInstance.api.login(
                    LoginRequest(username, password)
                )

                // Sauvegarde du token
                token = "Bearer ${tokenResponse.access_token}"

                // 2. Récupération des infos utilisateur (GET /api/auth/me)
                // C'est ici que la magie opère !
                val userInfo = RetrofitInstance.api.getUserInfo(token!!)

                // Mise à jour des variables d'état
                currentUsername = userInfo.username
                currentEmail = userInfo.email ?: "Pas d'email" // Gère le null


                // 3. Récupération des lampes (GET /api/devices)
                val apiDevices = RetrofitInstance.api.getDevices(token!!)

                lamps.value = apiDevices.map { device ->
                    SmartLamp(
                        id = device.id,
                        name = device.name,
                        isOn = device.is_active,
                        brightness = device.intensity ?: 0.5f
                    )
                }

                // Tout est chargé, on ouvre l'app
                isLoggedIn = true

            } catch (e: Exception) {
                e.printStackTrace()
                errorMessage.value = "Erreur : ${e.localizedMessage}"
                isLoggedIn = false
            } finally {
                isLoading.value = false
            }
        }
    }

    fun logout() {
        debounceJob?.cancel()

        // Nettoyage complet
        token = null
        currentUsername = ""
        currentEmail = ""
        lamps.value = emptyList()
        errorMessage.value = null

        isLoggedIn = false
    }
}