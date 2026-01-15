package com.example.smarthome

import androidx.compose.runtime.mutableStateOf
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.launch




class SmartHomeViewModel : ViewModel() {

    var lamps = mutableStateOf<List<SmartLamp>>(emptyList())
        private set

    var errorMessage = mutableStateOf<String?>(null)
        private set


    init {
        // Au démarrage, on tente de se connecter et charger les lampes
        loadData()
    }

    private fun loadData() {
        viewModelScope.launch {
            try {
                errorMessage.value = null

                val tokenResponse = RetrofitInstance.api.login(LoginRequest("admin", "admin123"))

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
        // Ici, il faudra ajouter un appel API @PUT ou @PATCH
        // Pour l'instant on met à jour localement pour que l'UI réagisse
        val currentList = lamps.value.toMutableList()
        val index = currentList.indexOfFirst { it.id == lamp.id }
        if (index != -1) {
            currentList[index] = lamp
            lamps.value = currentList
        }
    }

}