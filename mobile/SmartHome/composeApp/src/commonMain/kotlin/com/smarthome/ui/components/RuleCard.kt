package com.smarthome.ui.components

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedCard
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp

@Composable
fun RuleCard(
    ruleName: String,
    condition: String,
    action: String
) {
    var isEnabled by remember { mutableStateOf(true) }

    OutlinedCard(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp, horizontal = 8.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier.fillMaxWidth()
            ) {
                Text(ruleName, style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
                Switch(checked = isEnabled, onCheckedChange = { isEnabled = it })
            }
            Text("SI: $condition", style = MaterialTheme.typography.bodyMedium, fontWeight = FontWeight.SemiBold)
            Text("ALORS: $action", style = MaterialTheme.typography.bodyMedium)
        }
    }
}
