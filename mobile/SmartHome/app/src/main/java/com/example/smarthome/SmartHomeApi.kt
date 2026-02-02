package com.example.smarthome

import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.POST
import retrofit2.http.PUT
import retrofit2.http.Path
import retrofit2.http.Query


// [NOUVEAU] Pour les infos utilisateur (/api/auth/me)
// Adapte les champs si ton API renvoie des noms différents (ex: "email" vs "mail")
data class UserResponse(
    val id: Int?,
    val username: String,
    val email: String?,     // Peut être null selon l'API
    val full_name: String?  // Peut être null selon l'API
)
interface SmartHomeApi {
    // Attention: Je suppose que le endpoint de login est "/token" (standard FastAPI)
    // Si c'est autre chose (ex: /auth/login), change-le ici.
    @POST("api/auth/login")
    suspend fun login(@Body request: LoginRequest): TokenResponse

    @GET("/api/devices/")
    suspend fun getDevices(@Header("Authorization") token: String): List<ApiDevice>

    // --- AJOUTE CECI ---
    @PUT("api/devices/{device_id}/brightness")
    suspend fun updateBrightness(
        @Header("Authorization") token: String,
        @Path("device_id") deviceId: Int,
        @Query("intensity") intensity: Float // On envoie la valeur (0.0 à 1.0)
    )

    @GET("api/auth/me")
    suspend fun getUserInfo(@Header("Authorization") token: String): UserResponse
}