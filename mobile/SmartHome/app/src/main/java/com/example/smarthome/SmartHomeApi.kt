package com.example.smarthome

import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.POST

interface SmartHomeApi {
    // Attention: Je suppose que le endpoint de login est "/token" (standard FastAPI)
    // Si c'est autre chose (ex: /auth/login), change-le ici.
    @POST("api/auth/login")
    suspend fun login(@Body request: LoginRequest): TokenResponse

    @GET("/api/devices/")
    suspend fun getDevices(@Header("Authorization") token: String): List<ApiDevice>
}