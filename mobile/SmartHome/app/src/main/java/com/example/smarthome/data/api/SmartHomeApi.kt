package com.example.smarthome.data.api

import com.example.smarthome.data.model.*
import retrofit2.http.*

data class UserResponse(
    val id: Int?,
    val username: String,
    val email: String?,
    val full_name: String? = null,
    val role: String? = null,
    val created_at: String? = null
)

data class DeviceStateRequest(
    val state: Boolean,
    val brightness: Int
)

data class UpdateRuleRequest(
    val enabled: Boolean
)

interface SmartHomeApi {
    @POST("api/auth/login")
    suspend fun login(@Body request: LoginRequest): TokenResponse

    @GET("api/devices/")
    suspend fun getDevices(@Header("Authorization") token: String): List<ApiDevice>

    @POST("api/devices/")
    suspend fun addDevice(
        @Header("Authorization") token: String,
        @Body request: AddDeviceRequest
    ): ApiDevice

    @DELETE("api/devices/{device_id}")
    suspend fun deleteDevice(
        @Header("Authorization") token: String,
        @Path("device_id") deviceId: Int
    )

    @PUT("api/devices/{device_id}/brightness")
    suspend fun updateBrightness(
        @Header("Authorization") token: String,
        @Path("device_id") deviceId: Int,
        @Query("intensity") intensity: Float
    )

    @PUT("api/devices/{device_id}/state")
    suspend fun updateState(
        @Header("Authorization") token: String,
        @Path("device_id") deviceId: Int,
        @Body request: DeviceStateRequest
    ): ApiDevice

    @GET("api/devices/{device_id}/sensor")
    suspend fun getSensor(
        @Header("Authorization") token: String,
        @Path("device_id") deviceId: Int
    ): ApiSensor

    @GET("api/smart-dimming/status")
    suspend fun getSmartDimmingStatus(@Header("Authorization") token: String): com.example.smarthome.data.model.SmartDimmingStatus

    @GET("api/smart-dimming/adjustments")
    suspend fun getSmartDimmingHistory(@Header("Authorization") token: String): List<com.example.smarthome.data.model.SmartDimmingAdjustment>

    @PUT("api/smart-dimming/enable")
    suspend fun updateSmartDimmingStatus(
        @Header("Authorization") token: String,
        @Body request: com.example.smarthome.data.model.SmartDimmingRequest
    ): com.example.smarthome.data.model.SmartDimmingStatus

    @GET("api/events")
    suspend fun getEvents(@Header("Authorization") token: String): List<com.example.smarthome.data.model.ApiEvent>

    @GET("api/auth/me")
    suspend fun getUserInfo(@Header("Authorization") token: String): UserResponse

    @POST("api/auth/register")
    suspend fun register(@Body request: RegisterRequest): UserResponse

    @GET("api/ai/current-scenario")
    suspend fun getAICurrentScenario(@Header("Authorization") token: String): AIScenarioResponse

    // --- Rules ---
    @GET("api/rules/")
    suspend fun getRules(@Header("Authorization") token: String): List<RuleResponse>

    @POST("api/rules/")
    suspend fun createRule(
        @Header("Authorization") token: String,
        @Body request: RuleRequest
    ): RuleResponse

    @PUT("api/rules/{rule_id}")
    suspend fun updateRule(
        @Header("Authorization") token: String,
        @Path("rule_id") ruleId: Int,
        @Body request: UpdateRuleRequest
    ): RuleResponse

    @DELETE("api/rules/{rule_id}")
    suspend fun deleteRule(
        @Header("Authorization") token: String,
        @Path("rule_id") ruleId: Int
    )
}
