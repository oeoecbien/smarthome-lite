package com.example.smarthome.ui.screens


import androidx.compose.animation.Crossfade
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.pulltorefresh.PullToRefreshBox
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.smarthome.darkTextFieldColors
import com.example.smarthome.data.model.*
import com.example.smarthome.ui.components.*
import com.example.smarthome.ui.theme.PrimaryBlue
import com.example.smarthome.ui.viewmodel.SmartHomeViewModel


@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(
    modifier: Modifier = Modifier,
    viewModel: SmartHomeViewModel = viewModel(),
    selectedLampId: Int?,
    onLampSelect: (Int?) -> Unit,
    showAddDevice: Boolean,
    onShowAddDeviceChange: (Boolean) -> Unit
) {
    val devices by viewModel.devices
    val isDevicesLoading by viewModel.isDevicesLoading

    if (showAddDevice) {
        AddDeviceScreen(
            viewModel = viewModel,
            onBack = { onShowAddDeviceChange(false) }
        )
    } else {
        // Navigation entre Liste et Détail
        Crossfade(targetState = selectedLampId, label = "PageTransition") { lampId ->
            if (lampId == null) {
                // --- VUE PRINCIPALE (Design de l'image) ---
                PullToRefreshBox(
                    isRefreshing = isDevicesLoading,
                    onRefresh = { viewModel.refreshDevices() },
                    modifier = modifier
                        .fillMaxSize()
                        .background(MaterialTheme.colorScheme.background)


                ) {
                    Column(
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(horizontal = 20.dp)
                    ) {
                        // 1. En-tête (Profil + Notif)
                        HeaderSection(
                            name = "${viewModel.currentUsername}",
                            onAddClick = { onShowAddDeviceChange(true) }
                        )

                        Spacer(modifier = Modifier.height(24.dp))

                        // 4. Section Devices (Grille)
                        Text(
                            text = "Mes appareils",
                            style = MaterialTheme.typography.titleLarge,
                            color = MaterialTheme.colorScheme.primary,
                            fontWeight = FontWeight.Bold
                        )
                        Spacer(modifier = Modifier.height(16.dp))

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
                                onUpdate = { viewModel.updateDevice(it) },
                                viewModel = viewModel
                            )
                        }
                        is SmartSensor -> {
                            SensorControlScreen(
                                sensor = activeDevice,
                                onBack = { onLampSelect(null) },
                                viewModel = viewModel
                            )
                        }
                    }
                }
            }
        }
    }
}
