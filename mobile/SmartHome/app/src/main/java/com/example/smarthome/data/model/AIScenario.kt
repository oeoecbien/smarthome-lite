package com.example.smarthome.data.model

import com.google.gson.annotations.SerializedName

data class AIScenarioResponse(
    @SerializedName("scenario")
    val scenario: Int,
    @SerializedName("scenario_name")
    val scenarioName: String,
    @SerializedName("confidence")
    val confidence: Double,
    @SerializedName("method")
    val method: String,
    @SerializedName("context")
    val context: AIContext
)

data class AIContext(
    @SerializedName("hour")
    val hour: Int,
    @SerializedName("day_of_week")
    val dayOfWeek: Int,
    @SerializedName("presence_detected")
    val presenceDetected: Boolean,
    @SerializedName("light_on")
    val lightOn: Boolean,
    @SerializedName("raspberry_pi_id")
    val raspberryPiId: String?,
    @SerializedName("detected_users")
    val detectedUsers: List<String>,
    @SerializedName("detected_usernames")
    val detectedUsernames: List<String>,
    @SerializedName("user_count")
    val userCount: Int
)
