package com.example.smarthome

data class ApiDevice(
    val id: Int,
    val name: String,

    // CORRECTION : "state" au lieu de "is_active"
    val state: Boolean,

    // CORRECTION : "brightness" (Int) au lieu de "intensity" (Float)
    // Le JSON renvoie 13 (entier), probablement sur 100.
    val brightness: Int?
)
