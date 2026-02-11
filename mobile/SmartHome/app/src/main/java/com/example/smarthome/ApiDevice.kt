package com.example.smarthome

data class ApiDevice(
    val id: Int,
    val name: String,
    val is_active: Boolean, // J'imagine que l'API renvoie is_active ou similaire
    val intensity: Float? = 0f // Optionnel
)
