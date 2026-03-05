package com.example.smarthome.ui.viewmodel

import com.example.smarthome.data.model.*
import com.example.smarthome.data.repository.RepositoryProvider

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.isActive
import retrofit2.HttpException


class SmartHomeViewModel : ViewModel() {

    // ─── Données exposées à l'UI ─────────────────────────────────────────────────
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

    var currentEmail by mutableStateOf("")
        private set

    // --- Smart Dimming ---
    var smartDimmingStatus = mutableStateOf<SmartDimmingStatus?>(null)
        private set

    var smartDimmingHistory = mutableStateOf<List<SmartDimmingAdjustment>>(emptyList())
        private set

    // --- Événements ---
    var events = mutableStateOf<List<com.example.smarthome.data.model.ApiEvent>>(emptyList())
        private set

    // ─── État interne ─────────────────────────────────────────────────────────────
    private var token: String? = null
    private var debounceJob: Job? = null
    private var refreshJob: Job? = null
    
    // Garde en mémoire l'heure (en millisecondes) de la dernière modification par l'utilisateur
    // pour chaque appareil. K=Id Device, V=Timestamp
    private val lastUpdateMap = mutableMapOf<Int, Long>()
    
    // Durée pendant laquelle on ignore les données venant du serveur après une modif locale (5s)
    private val IGNORE_SERVER_DELAY_MS = 5000L

    // Le repository est fourni par RepositoryProvider (fake ou réel selon USE_FAKE)
    private val repository = RepositoryProvider.repository

    // ─── Login ────────────────────────────────────────────────────────────────────
    fun login(username: String, password: String) {
        viewModelScope.launch {
            try {
                isLoading.value = true
                errorMessage.value = null

                // 1. Authentification → récupère le token + les infos utilisateur
                val loginResult = repository.login(username, password)
                token = loginResult.token
                currentUsername = loginResult.userInfo.username
                currentEmail = loginResult.userInfo.email ?: ""

                // 2. Premier chargement des devices, Smart Dimming et Evénements
                fetchDevices()
                fetchSmartDimmingData()
                fetchEvents()

                isLoggedIn = true

                // 3. Actualisation automatique
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

    // ─── Mise à jour device ───────────────────────────────────────────────────────
    fun updateDevice(device: SmartDevice) {
        if (device !is SmartLight) return

        val currentList = devices.value.toMutableList()
        val index = currentList.indexOfFirst { it.id == device.id }
        if (index == -1) return

        val oldDevice = currentList[index]
        currentList[index] = device
        devices.value = currentList
        
        // On enregistre qu'on vient de modifier cet appareil
        lastUpdateMap[device.id] = System.currentTimeMillis()

        if (oldDevice is SmartLight) {
            sendUpdateToApi(device, oldDevice)
        }
    }

    private fun sendUpdateToApi(newLamp: SmartLight, oldLamp: SmartLight) {
        debounceJob?.cancel()
        debounceJob = viewModelScope.launch {
            try {
                if (token == null) return@launch

                // CAS 1 : L'interrupteur (ON/OFF) a changé
                if (newLamp.isOn != oldLamp.isOn) {
                    val brightnessInt = (newLamp.brightness * 100).toInt()
                    repository.updateState(
                        token      = token!!,
                        deviceId   = newLamp.id,
                        state      = newLamp.isOn,
                        brightness = brightnessInt
                    )
                }

                // CAS 2 : La luminosité a changé (lampe allumée)
                if (newLamp.brightness != oldLamp.brightness && newLamp.isOn) {
                    repository.updateBrightness(
                        token    = token!!,
                        deviceId = newLamp.id,
                        intensity = newLamp.brightness
                    )
                }

            } catch (e: Exception) {
                e.printStackTrace()
                // Rollback en cas d'erreur
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

    // ─── Fetch devices ────────────────────────────────────────────────────────────
    private suspend fun fetchDevices() {
        if (token == null) return
        val serverDevices = repository.getDevices(token!!)
        
        val currentTime = System.currentTimeMillis()
        val currentLocalDevices = devices.value.associateBy { it.id }
        
        // On merge les devices du serveur avec nos devices locaux
        val mergedDevices = serverDevices.map { serverDevice ->
            val lastUpdateTime = lastUpdateMap[serverDevice.id] ?: 0L
            val isRecentlyUpdatedLocally = (currentTime - lastUpdateTime) < IGNORE_SERVER_DELAY_MS
            
            if (isRecentlyUpdatedLocally && currentLocalDevices.containsKey(serverDevice.id)) {
                // Le serveur n'a peut-être pas encore la bonne valeur, on garde notre valeur locale
                currentLocalDevices[serverDevice.id]!!
            } else {
                // Le délai est passé ou pas de modif locale récente, on prend la valeur du serveur
                serverDevice
            }
        }
        
        devices.value = mergedDevices
    }

    // ─── Fetch Smart Dimming ──────────────────────────────────────────────────────
    private suspend fun fetchSmartDimmingData() {
        if (token == null) return
        try {
            smartDimmingStatus.value = repository.getSmartDimmingStatus(token!!)
            smartDimmingHistory.value = repository.getSmartDimmingHistory(token!!)
        } catch (e: Exception) {
            e.printStackTrace()
            // Optionnel : ne pas crasher l'app si ces endpoints manquent
        }
    }

    // ─── Update Smart Dimming ─────────────────────────────────────────────────────
    fun toggleSmartDimming(enabled: Boolean) {
        viewModelScope.launch {
            try {
                if (token == null) return@launch
                
                // Active le bouton immédiatement (Optimistic UI)
                val currentStatus = smartDimmingStatus.value
                if (currentStatus != null) {
                    smartDimmingStatus.value = currentStatus.copy(enabled = enabled)
                }

                val newStatus = repository.updateSmartDimmingStatus(token!!, enabled)
                smartDimmingStatus.value = newStatus
                
                // Recharge l'historique potentiellement mis à jour
                smartDimmingHistory.value = repository.getSmartDimmingHistory(token!!)
            } catch (e: Exception) {
                e.printStackTrace()
                errorMessage.value = "Erreur Smart Dimming : ${e.localizedMessage}"
                // Rollback (re-fetch)
                fetchSmartDimmingData()
            }
        }
    }

    // ─── Fetch Events ─────────────────────────────────────────────────────────────
    private suspend fun fetchEvents() {
        if (token == null) return
        try {
            events.value = repository.getEvents(token!!)
        } catch (e: Exception) {
            e.printStackTrace()
            // Optionnel : on ignore silencieusement si l'endpoint échoue
        }
    }

    // ─── Auto-refresh ─────────────────────────────────────────────────────────────
    private fun startAutoRefresh() {
        refreshJob?.cancel()
        refreshJob = viewModelScope.launch {
            while (isActive && isLoggedIn) {
                delay(6000)
                if (debounceJob?.isActive == true) continue
                try {
                    if (token != null) {
                        fetchDevices()
                        fetchSmartDimmingData()
                        fetchEvents()
                    }
                } catch (e: Exception) {
                    e.printStackTrace()
                }
            }
        }
    }

    // ─── Logout ───────────────────────────────────────────────────────────────────
    fun logout() {
        debounceJob?.cancel()
        refreshJob?.cancel()

        token = null
        currentUsername = ""
        currentEmail = ""
        devices.value = emptyList()
        errorMessage.value = null
        isLoggedIn = false
    }

    // ─── Registration ─────────────────────────────────────────────────────────────
    var registrationSuccess = mutableStateOf(false)
        private set

    var registrationError = mutableStateOf<String?>(null)
        private set

    var isRegistering = mutableStateOf(false)
        private set

    fun register(username: String, email: String, password: String) {
        viewModelScope.launch {
            try {
                isRegistering.value = true
                registrationError.value = null
                registrationSuccess.value = false


                repository.register(username, email, password)

                registrationSuccess.value = true
            } catch (e: Exception) {
                e.printStackTrace()
                if (e is HttpException && e.code() == 422) {
                    val errorBody = e.response()?.errorBody()?.string()
                    registrationError.value = "Données invalides : $errorBody"
                } else {
                    registrationError.value = "Erreur inscription : ${e.localizedMessage}"
                }
            } finally {
                isRegistering.value = false
            }
        }
    }

    fun resetRegistration() {
        registrationSuccess.value = false
        registrationError.value = null
    }
}
