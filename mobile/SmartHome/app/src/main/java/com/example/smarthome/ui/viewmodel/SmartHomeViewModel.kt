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

    // ─── État interne ─────────────────────────────────────────────────────────────
    private var token: String? = null
    private var debounceJob: Job? = null
    private var refreshJob: Job? = null

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

                // 2. Premier chargement des devices
                fetchDevices()

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
        devices.value = repository.getDevices(token!!)
    }

    // ─── Auto-refresh ─────────────────────────────────────────────────────────────
    private fun startAutoRefresh() {
        refreshJob?.cancel()
        refreshJob = viewModelScope.launch {
            while (isActive && isLoggedIn) {
                delay(6000)
                if (debounceJob?.isActive == true) continue
                try {
                    if (token != null) fetchDevices()
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
}