package com.example.smarthome.data.repository

/**
 * Point d'entrée unique pour obtenir le repository.
 *
 * ══════════════════════════════════════════════════════════
 *  ⚙️  POUR BASCULER ENTRE LES DONNÉES FAKE ET LA VRAIE API
 *      → Changer la valeur de USE_FAKE ci-dessous :
 *
 *      true  = données fake (pas besoin de serveur)
 *      false = vraie API Retrofit
 * ══════════════════════════════════════════════════════════
 */
object RepositoryProvider {

    private const val USE_FAKE = true   // ← changer ici pour switcher

    val repository: SmartHomeRepository by lazy {
        if (USE_FAKE) FakeSmartHomeRepository()
        else RealSmartHomeRepository()
    }
}
