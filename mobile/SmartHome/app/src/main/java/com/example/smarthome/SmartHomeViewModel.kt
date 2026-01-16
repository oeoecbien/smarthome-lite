package com.example.smarthome

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.launch




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


    init {
        // Au démarrage, on tente de se connecter et charger les lampes
        loadData()
    }

    fun loadData() {
        viewModelScope.launch {
            try {
                errorMessage.value = null

                val tokenResponse = RetrofitInstance.api.login(LoginRequest("jean", "Password123"))

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

    fun login(username: String, password: String) {
        viewModelScope.launch {
            try {
                isLoading.value = true
                errorMessage.value = null // Reset erreur précédente

                // 1. Connexion (Login)
                val tokenResponse = RetrofitInstance.api.login(
                    LoginRequest(username, password)
                )

                val bearerToken = "Bearer ${tokenResponse.access_token}"

                // 2. Récupération des devices
                // Note : Assure-toi que le @GET est bien sur "api/devices" ou "devices" selon ton test précédent
                val apiDevices = RetrofitInstance.api.getDevices(bearerToken)

                // 3. Conversion
                lamps.value = apiDevices.map { device ->
                    SmartLamp(
                        id = device.id,
                        name = device.name,
                        isOn = device.is_active,
                        brightness = device.intensity ?: 0.5f
                    )
                }

                // 4. Sauvegarder le nom pour la fonction HomeScreen()
                currentUsername = username

                // 5. Si tout est OK, on valide la connexion
                isLoggedIn = true



            } catch (e: Exception) {
                e.printStackTrace()
                // Afficher l'erreur à l'utilisateur (ex: 404, mot de passe incorrect...)
                errorMessage.value = "Échec connexion : ${e.localizedMessage}"
                isLoggedIn = false
            } finally {
                isLoading.value = false
            }
        }
    }

}