package com.example.smarthome.data.api

import com.example.smarthome.BuildConfig
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

// 3. Singleton pour la connexion
object RetrofitInstance {
    private val BASE_URL: String = BuildConfig.API_BASE_URL

    val api: SmartHomeApi by lazy {
        Retrofit.Builder()
            .baseUrl(BASE_URL)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(SmartHomeApi::class.java)
    }
}