package com.example.smarthome

data class ApiDevice(
    val id: Int,
    val name: String,

    // CORRECTION : "state" au lieu de "is_active"
    val state: Boolean,

    // CORRECTION : "brightness" (Int) au lieu de "intensity" (Float)
    // Le JSON renvoie 13 (entier), probablement sur 100.
    val brightness: Int?,
    val type: String?
)
data class ApiSensor(
    val success: Boolean,
    val device_id: Int,
    val temperature_c: Float?,
    val humidity: Int?,
    val illuminance_lux: Int?,
    val motion: Boolean?,
    val battery_percent: Int?
)
