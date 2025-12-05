package com.smarthome.ui.components

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun DashboardHeader(
    // Fake data for now
    scenario: String,
    ambientLight: String,
    smartDimmingStatus: String
) {
    Column(modifier = Modifier.padding(16.dp)) {
        Text("Scénario actuel: $scenario", style = MaterialTheme.typography.titleMedium)
        Text("Luminosité ambiante: $ambientLight", style = MaterialTheme.typography.bodyMedium)
        Text("Smart Dimming: $smartDimmingStatus", style = MaterialTheme.typography.bodyMedium)
    }
}
