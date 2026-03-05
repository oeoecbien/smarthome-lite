package com.example.smarthome.data.model

import com.google.gson.annotations.SerializedName

data class RuleResponse(
    val id: Int,
    val name: String,
    val description: String,
    val enabled: Boolean,
    val priority: Int,
    val condition: RuleCondition,
    val action: RuleAction,
    @SerializedName("created_at") val createdAt: String,
    @SerializedName("updated_at") val updatedAt: String
)

data class RuleRequest(
    val name: String,
    val description: String,
    val enabled: Boolean,
    val priority: Int,
    val condition: RuleCondition,
    val action: RuleAction
)

data class RuleCondition(
    val type: String, // e.g., "AND", "OR", or individual types if simple
    val conditions: List<ConditionItem>? = null
)

data class ConditionItem(
    val type: String, // "time", "presence", "light", etc.
    val value: Any,   // Can be List<String> for time, Boolean for presence, Int for light
    val operator: String? = null // "between", "<", ">", "=="
)

data class RuleAction(
    val action: String, // "set_brightness", "toggle_state", etc.
    @SerializedName("device_id") val deviceId: Int,
    val brightness: Int? = null,
    val state: Boolean? = null
)
