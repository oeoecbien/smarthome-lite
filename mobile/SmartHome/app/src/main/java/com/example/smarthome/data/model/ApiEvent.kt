package com.example.smarthome.data.model

data class ApiEvent(
    val id: Int,
    val device_id: Int,
    val device_name: String,
    val event_type: String,
    val value: String,
    val source: String,
    val timestamp: String
)
