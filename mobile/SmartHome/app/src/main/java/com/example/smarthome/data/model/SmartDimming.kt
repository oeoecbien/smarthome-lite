package com.example.smarthome.data.model

data class SmartDimmingStatus(
    val enabled: Boolean,
    val adjustments_today: Int,
    val active_devices: List<Int>
)

data class SmartDimmingAdjustment(
    val id: Int,
    val device_id: Int,
    val device_name: String,
    val scenario: Int,
    val brightness_before: Int,
    val brightness_after: Int,
    val reason: String,
    val timestamp: String
)

data class SmartDimmingRequest(
    val enabled: Boolean
)
