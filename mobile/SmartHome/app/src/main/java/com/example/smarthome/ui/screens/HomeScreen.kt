package com.example.smarthome.ui.screens

import androidx.compose.animation.Crossfade
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.smarthome.data.model.*
import com.example.smarthome.ui.components.*
import com.example.smarthome.ui.viewmodel.SmartHomeViewModel


@Composable
fun HomeScreen(
    modifier: Modifier = Modifier,
    viewModel: SmartHomeViewModel = viewModel(),
    selectedLampId: Int?,
    onLampSelect: (Int?) -> Unit
) {
    val devices by viewModel.devices
    val isDevicesLoading by viewModel.isDevicesLoading
    val error by viewModel.errorMessage

    // Navigation entre Liste et Détail
    Crossfade(targetState = selectedLampId, label = "PageTransition") { lampId ->
        if (lampId == null) {
            // --- VUE PRINCIPALE (Design de l'image) ---
            Column(
                modifier = modifier
                    .fillMaxSize()
                    .background(MaterialTheme.colorScheme.background) // Fond sombre global
                    .padding(horizontal = 20.dp)
            ) {
                // 1. En-tête (Profil + Notif)
                HeaderSection(name = "${viewModel.currentUsername}")

                Spacer(modifier = Modifier.height(24.dp))

                // 4. Section Devices (Grille)
                Text(
                    text = "Mes appareils",
                    style = MaterialTheme.typography.titleLarge,
                    color = MaterialTheme.colorScheme.primary,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.height(16.dp))

                if (isDevicesLoading) {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .weight(1f),
                        contentAlignment = Alignment.Center
                    ) {
                        CircularProgressIndicator(
                            color = MaterialTheme.colorScheme.primary
                        )
                    }
                } else {
                    // Grille intelligente
                    DeviceGrid(
                        devices = devices,
                        onLampClick = { onLampSelect(it.id) },
                        onSensorClick = { onLampSelect(it.id) }, // Réutilise le même ID state
                        onToggleLamp = { lamp, newState ->
                             viewModel.updateDevice(lamp.copy(isOn = newState))
                        }
                    )
                }
            }
        } else {
            // --- VUE DÉTAIL ---
            val activeDevice = devices.find { it.id == lampId }
            if (activeDevice != null) {
                when (activeDevice) {
                    is SmartLight -> {
                        LampControlScreen(
                            lamp = activeDevice,
                            onBack = { onLampSelect(null) },
                            onUpdate = { viewModel.updateDevice(it) }
                        )
                    }
                    is SmartSensor -> {
                         SensorControlScreen(
                            sensor = activeDevice,
                            onBack = { onLampSelect(null) }
                        )
                    }
                }
            }
        }
    }
}
