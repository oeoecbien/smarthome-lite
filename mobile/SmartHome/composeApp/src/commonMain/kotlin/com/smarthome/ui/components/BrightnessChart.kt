package com.smarthome.ui.components

import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp

@Composable
fun BrightnessChart() {
    Column(modifier = Modifier.padding(16.dp)) {
        Text("Évolution sur 24h", style = MaterialTheme.typography.titleMedium)
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(200.dp)
                .border(1.dp, Color.Gray),
            contentAlignment = Alignment.Center
        ) {
            Text("[Graphique: Luminosité ambiante vs Intensité artificielle]", style = MaterialTheme.typography.bodySmall)
        }
    }
}
