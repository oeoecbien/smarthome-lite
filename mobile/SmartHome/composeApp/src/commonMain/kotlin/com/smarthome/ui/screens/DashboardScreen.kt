package com.smarthome.ui.screens

import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.smarthome.ui.components.DashboardHeader
import com.smarthome.ui.components.DeviceCard

// A temporary data class to represent a device
data class Device(val name: String, val isDimmable: Boolean)

// A fake list of devices for UI development
private val fakeDevices = listOf(
    Device("Lampe Salon", isDimmable = true),
    Device("Prise Cuisine", isDimmable = false),
    Device("Lampe Bureau", isDimmable = true),
    Device("Lampe Chambre", isDimmable = false),
    Device("Prise Multimédia", isDimmable = false),
    Device("Lumière d'ambiance", isDimmable = true)
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DashboardScreen(modifier: Modifier = Modifier) {
    Scaffold(
        modifier = modifier,
        topBar = { TopAppBar(title = { Text("Tableau de Bord") }) }
    ) { paddingValues ->
        BoxWithConstraints(modifier = Modifier.padding(paddingValues)) {
            if (maxWidth < 600.dp) { // Portrait or narrow screen
                LazyColumn {
                    item {
                        DashboardHeader(
                            scenario = "Mode Jour",
                            ambientLight = "550 lux",
                            smartDimmingStatus = "Actif"
                        )
                    }
                    items(fakeDevices) { device ->
                        DeviceCard(name = device.name, isDimmable = device.isDimmable)
                    }
                }
            } else { // Landscape or wide screen
                LazyVerticalGrid(
                    columns = GridCells.Adaptive(minSize = 300.dp) // Each item has a min width of 300.dp
                ) {
                    // You might want a different header for grid layout
                    // For now, we omit it for simplicity.
                    items(fakeDevices) { device ->
                        DeviceCard(name = device.name, isDimmable = device.isDimmable)
                    }
                }
            }
        }
    }
}
