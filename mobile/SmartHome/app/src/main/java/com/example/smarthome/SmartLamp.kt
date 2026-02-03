package com.example.smarthome

// --- Modèle de données simple pour une lampe ---
data class SmartLamp(
    val id: Int,
    val name: String,
    val isOn: Boolean,
    val brightness: Float // 0.0 à 1.0
)
