package com.smarthome.ui.screens

import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Divider
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.smarthome.ui.components.AdjustmentHistoryItem
import com.smarthome.ui.components.BrightnessChart

private data class Adjustment(val time: String, val action: String, val reason: String)

private val fakeHistory = listOf(
    Adjustment("14:32", "Intensité réduite à 25%", "Lumière naturelle élevée (800 lux)"),
    Adjustment("12:15", "Intensité augmentée à 55%", "Ciel couvert (250 lux)"),
    Adjustment("09:10", "Intensité réduite à 30%", "Lumière du matin suffisante (600 lux)")
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SmartDimmingScreen(modifier: Modifier = Modifier) {
    Scaffold(
        modifier = modifier,
        topBar = { TopAppBar(title = { Text("Smart Dimming") }) }
    ) {
        LazyColumn(modifier = Modifier.padding(it)) {
            item {
                BrightnessChart()
            }
            item {
                Text(
                    "Derniers ajustements automatiques",
                    style = MaterialTheme.typography.titleMedium,
                    modifier = Modifier.padding(16.dp)
                )
                Divider()
            }
            items(fakeHistory) { adjustment ->
                AdjustmentHistoryItem(
                    time = adjustment.time,
                    action = adjustment.action,
                    reason = adjustment.reason
                )
                Divider()
            }
        }
    }
}
