package com.smarthome.ui.components

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun AdjustmentHistoryItem(
    time: String,
    action: String,
    reason: String
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 8.dp)
    ) {
        Text("$time - $action", style = MaterialTheme.typography.bodyLarge)
        Text("Raison: $reason", style = MaterialTheme.typography.bodyMedium)
    }
}
