package com.example.smarthome

// --- Modèle unifié pour tous les appareils ---
sealed class SmartDevice {
    abstract val id: Int
    abstract val name: String
    abstract val type: String
}

data class SmartLight(
    override val id: Int,
    override val name: String,
    val isOn: Boolean,
    val brightness: Float, // 0.0 à 1.0
    override val type: String = "light"
) : SmartDevice()

data class SmartSensor(
    override val id: Int,
    override val name: String,
    val temperature: Float,
    val humidity: Int,
    val illuminance: Int,
    val motion: Boolean,
    val battery: Int,
    override val type: String = "sensor"
) : SmartDevice()
