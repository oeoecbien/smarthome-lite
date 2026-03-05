package com.example.smarthome.data.api

import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

// 3. Singleton pour la connexion
object RetrofitInstance {
    private const val BASE_URL = "http://10.109.150.75:8000/"

    val api: SmartHomeApi by lazy {
        Retrofit.Builder()
            .baseUrl(BASE_URL)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(SmartHomeApi::class.java)
    }
}