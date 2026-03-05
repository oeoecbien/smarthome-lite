package com.example.smarthome.ui.viewmodel

import com.example.smarthome.data.model.*
import com.example.smarthome.data.repository.RepositoryProvider
import com.example.smarthome.data.api.TokenManager

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.isActive
import kotlinx.coroutines.flow.first
import retrofit2.HttpException


class SmartHomeViewModel : ViewModel() {

    // ─── Données exposées à l'UI ─────────────────────────────────────────────────
    var devices = mutableStateOf<List<SmartDevice>>(emptyList())
        private set

    var errorMessage = mutableStateOf<String?>(null)
        private set

    var isLoading = mutableStateOf(false)
        private set

    var isDevicesLoading = mutableStateOf(false)
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

    // --- Intelligence Artificielle ---
    var aiScenario = mutableStateOf<AIScenarioResponse?>(null)
        private set
    
    var isAILoading = mutableStateOf(false)
        private set

    // --- Règles ---
    var rules = mutableStateOf<List<RuleResponse>>(emptyList())
        private set
    
    var isRulesLoading = mutableStateOf(false)
        private set

    // ─── État interne ─────────────────────────────────────────────────────────────
    private var token: String? = null
    private var debounceJob: Job? = null
    private var refreshJob: Job? = null
    private var tokenManager: TokenManager? = null
    
    private val lastUpdateMap = mutableMapOf<Int, Long>()
    private val IGNORE_SERVER_DELAY_MS = 5000L

    private val repository = RepositoryProvider.repository

    // ─── Initialisation ───────────────────────────────────────────────────────────
    fun initAuth(manager: TokenManager) {
        this.tokenManager = manager
        viewModelScope.launch {
            val savedToken = manager.token.first()
            val savedUsername = manager.username.first()
            val savedEmail = manager.email.first()

            if (!savedToken.isNullOrBlank()) {
                token = savedToken
                currentUsername = savedUsername ?: ""
                currentEmail = savedEmail ?: ""
                isLoggedIn = true
                
                // Charger les données
                refreshDevices()
                startAutoRefresh()
            }
        }
    }

    // ─── Login ────────────────────────────────────────────────────────────────────
    fun login(username: String, password: String) {
        viewModelScope.launch {
            try {
                isLoading.value = true
                errorMessage.value = null

                val loginResult = repository.login(username, password)
                token = loginResult.token
                currentUsername = loginResult.userInfo.username
                currentEmail = loginResult.userInfo.email ?: ""

                // Sauvegarder le token
                tokenManager?.saveAuthData(token!!, currentUsername, currentEmail)

                isLoggedIn = true

                isDevicesLoading.value = true
                launch { 
                    fetchDevices() 
                    isDevicesLoading.value = false
                }
                launch { fetchSmartDimmingData() }
                launch { fetchEvents() }
                launch { fetchAIScenario() }
                launch { fetchRules() }

                startAutoRefresh()

            } catch (e: Exception) {
                e.printStackTrace()
                if (e is HttpException) {
                    errorMessage.value = when (e.code()) {
                        401 -> "Identifiants incorrects."
                        else -> "Erreur HTTP ${e.code()}"
                    }
                } else {
                    errorMessage.value = "Erreur de connexion."
                }
                isLoggedIn = false
            } finally {
                isLoading.value = false
            }
        }
    }

    // ─── Intelligence Artificielle ──────────────────────────────────────────────
    fun fetchAIScenario() {
        if (token == null) return
        viewModelScope.launch {
            try {
                isAILoading.value = true
                aiScenario.value = repository.getCurrentScenario(token!!)
            } catch (e: Exception) {
                e.printStackTrace()
                if (e is HttpException && e.code() == 401) handleUnauthorized()
            } finally {
                isAILoading.value = false
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

                if (newLamp.isOn != oldLamp.isOn) {
                    val brightnessInt = (newLamp.brightness * 100).toInt()
                    repository.updateState(
                        token      = token!!,
                        deviceId   = newLamp.id,
                        state      = newLamp.isOn,
                        brightness = brightnessInt
                    )
                }

                if (newLamp.brightness != oldLamp.brightness && newLamp.isOn) {
                    repository.updateBrightness(
                        token    = token!!,
                        deviceId = newLamp.id,
                        intensity = newLamp.brightness
                    )
                }

            } catch (e: Exception) {
                e.printStackTrace()
                if (e is HttpException && e.code() == 401) handleUnauthorized()
                errorMessage.value = "Erreur : ${e.localizedMessage}"
            }
        }
    }

    // ─── Ajouter un appareil ─────────────────────────────────────────────────────
    fun addDevice(name: String, type: String, gpioPin: Int, raspberryPiId: Int, onSuccess: () -> Unit) {
        viewModelScope.launch {
            try {
                if (token == null) return@launch
                isLoading.value = true
                errorMessage.value = null
                
                repository.addDevice(token!!, gpioPin, name, raspberryPiId, type)
                fetchDevices()
                onSuccess()
            } catch (e: Exception) {
                e.printStackTrace()
                if (e is HttpException && e.code() == 401) handleUnauthorized()
                errorMessage.value = "Erreur lors de l'ajout."
            } finally {
                isLoading.value = false
            }
        }
    }

    // ─── Refresh manuel ──────────────────────────────────────────────────────────
    fun refreshDevices() {
        if (token == null) return
        viewModelScope.launch {
            isDevicesLoading.value = true
            try {
                fetchDevices()
                fetchSmartDimmingData()
                fetchEvents()
                fetchAIScenario()
                fetchRules()
            } catch (e: Exception) {
                if (e is HttpException && e.code() == 401) handleUnauthorized()
            }
            isDevicesLoading.value = false
        }
    }

    // ─── Fetch devices ────────────────────────────────────────────────────────────
    private suspend fun fetchDevices() {
        if (token == null) return
        try {
            val serverDevices = repository.getDevices(token!!)
            val currentTime = System.currentTimeMillis()
            val currentLocalDevices = devices.value.associateBy { it.id }
            val mergedDevices = serverDevices.map { serverDevice ->
                val lastUpdateTime = lastUpdateMap[serverDevice.id] ?: 0L
                val isRecentlyUpdatedLocally = (currentTime - lastUpdateTime) < IGNORE_SERVER_DELAY_MS
                if (isRecentlyUpdatedLocally && currentLocalDevices.containsKey(serverDevice.id)) {
                    currentLocalDevices[serverDevice.id]!!
                } else {
                    serverDevice
                }
            }
            devices.value = mergedDevices
        } catch (e: Exception) {
            if (e is HttpException && e.code() == 401) handleUnauthorized()
            e.printStackTrace()
        }
    }

    // ─── Fetch Rules ─────────────────────────────────────────────────────────────
    fun fetchRules() {
        if (token == null) return
        viewModelScope.launch {
            try {
                isRulesLoading.value = true
                rules.value = repository.getRules(token!!)
            } catch (e: Exception) {
                if (e is HttpException && e.code() == 401) handleUnauthorized()
                e.printStackTrace()
            } finally {
                isRulesLoading.value = false
            }
        }
    }

    fun createRule(rule: RuleRequest, onSuccess: () -> Unit) {
        viewModelScope.launch {
            try {
                if (token == null) return@launch
                isLoading.value = true
                repository.createRule(token!!, rule)
                fetchRules()
                onSuccess()
            } catch (e: Exception) {
                if (e is HttpException && e.code() == 401) handleUnauthorized()
                e.printStackTrace()
                errorMessage.value = "Erreur lors de la création de la règle."
            } finally {
                isLoading.value = false
            }
        }
    }

    // ─── Fetch Smart Dimming ──────────────────────────────────────────────────────
    private suspend fun fetchSmartDimmingData() {
        if (token == null) return
        try {
            smartDimmingStatus.value = repository.getSmartDimmingStatus(token!!)
            smartDimmingHistory.value = repository.getSmartDimmingHistory(token!!)
        } catch (e: Exception) {
            if (e is HttpException && e.code() == 401) handleUnauthorized()
            e.printStackTrace()
        }
    }

    // ─── Update Smart Dimming ─────────────────────────────────────────────────────
    fun toggleSmartDimming(enabled: Boolean) {
        viewModelScope.launch {
            try {
                if (token == null) return@launch
                val currentStatus = smartDimmingStatus.value
                if (currentStatus != null) {
                    smartDimmingStatus.value = currentStatus.copy(enabled = enabled)
                }
                val newStatus = repository.updateSmartDimmingStatus(token!!, enabled)
                smartDimmingStatus.value = newStatus
                smartDimmingHistory.value = repository.getSmartDimmingHistory(token!!)
            } catch (e: Exception) {
                if (e is HttpException && e.code() == 401) handleUnauthorized()
                e.printStackTrace()
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
            if (e is HttpException && e.code() == 401) handleUnauthorized()
            e.printStackTrace()
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
                        fetchAIScenario()
                        fetchRules()
                    }
                } catch (e: Exception) {
                    if (e is HttpException && e.code() == 401) handleUnauthorized()
                    e.printStackTrace()
                }
            }
        }
    }

    private fun handleUnauthorized() {
        logout()
        errorMessage.value = "Session expirée. Veuillez vous reconnecter."
    }

    // ─── Logout ───────────────────────────────────────────────────────────────────
    fun logout() {
        debounceJob?.cancel()
        refreshJob?.cancel()
        
        viewModelScope.launch {
            tokenManager?.clearAuthData()
        }

        token = null
        currentUsername = ""
        currentEmail = ""
        devices.value = emptyList()
        errorMessage.value = null
        isLoggedIn = false
        isDevicesLoading.value = false
        aiScenario.value = null
        rules.value = emptyList()
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
                registrationError.value = "Erreur d'inscription."
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
