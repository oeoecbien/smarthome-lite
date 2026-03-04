package com.example.smarthome.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.example.smarthome.data.model.ApiEvent
import com.example.smarthome.ui.theme.NeonBlue
import com.example.smarthome.ui.theme.PrimaryBlue
import com.example.smarthome.ui.viewmodel.SmartHomeViewModel
import java.text.SimpleDateFormat
import java.util.Locale

@Composable
fun EventsScreen(viewModel: SmartHomeViewModel) {
    val events = viewModel.events.value

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .padding(horizontal = 20.dp)
    ) {
        Spacer(modifier = Modifier.height(24.dp))

        // --- Header Section ---
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "Événements",
                style = MaterialTheme.typography.headlineMedium,
                color = MaterialTheme.colorScheme.primary,
                fontWeight = FontWeight.Bold
            )
        }
        Text(
            text = "Historique d'activité de vos appareils",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.secondary
        )

        Spacer(modifier = Modifier.height(24.dp))

        if (events.isEmpty()) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = "Aucun événement récent",
                    color = MaterialTheme.colorScheme.secondary,
                    style = MaterialTheme.typography.bodyLarge
                )
            }
        } else {
            LazyColumn(
                modifier = Modifier.fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(12.dp),
                contentPadding = PaddingValues(bottom = 24.dp)
            ) {
                items(events) { event ->
                    EventItemCard(event)
                }
            }
        }
    }
}

@Composable
fun EventItemCard(event: ApiEvent) {
    // Déterminer l'icône et la couleur en fonction du type ou de la source
    val isAuto = event.source.contains("smart", ignoreCase = true) || event.source.contains("ml", ignoreCase = true)
    
    val icon = when {
        isAuto -> Icons.Default.AutoFixHigh
        event.event_type.contains("brightness") -> Icons.Default.Lightbulb
        event.event_type.contains("status") -> Icons.Default.ToggleOn
        else -> Icons.Default.Notifications
    }
    
    val iconTint = if (isAuto) NeonBlue else PrimaryBlue
    val iconBg = if (isAuto) NeonBlue.copy(alpha = 0.15f) else PrimaryBlue.copy(alpha = 0.15f)

    Card(
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.tertiary),
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Icône
            Box(
                modifier = Modifier
                    .size(44.dp)
                    .clip(RoundedCornerShape(12.dp))
                    .background(iconBg),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = icon,
                    contentDescription = null,
                    tint = iconTint,
                    modifier = Modifier.size(24.dp)
                )
            }

            Spacer(modifier = Modifier.width(16.dp))

            // Textes
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = event.device_name,
                    color = MaterialTheme.colorScheme.primary,
                    fontWeight = FontWeight.Bold,
                    style = MaterialTheme.typography.bodyLarge
                )
                
                Spacer(modifier = Modifier.height(4.dp))
                
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = formatEventValue(event.event_type, event.value),
                        color = MaterialTheme.colorScheme.secondary,
                        style = MaterialTheme.typography.bodyMedium
                    )
                    Text(
                        text = formatTimestampShort(event.timestamp),
                        color = MaterialTheme.colorScheme.secondary,
                        style = MaterialTheme.typography.bodySmall
                    )
                }
                
                Spacer(modifier = Modifier.height(4.dp))
                
                Text(
                    text = "Source: ${event.source}",
                    color = Color.Gray,
                    style = MaterialTheme.typography.bodySmall
                )
            }
        }
    }
}

private fun formatEventValue(type: String, value: String): String {
    return when {
        type.contains("brightness") -> "Luminosité : $value%"
        type.contains("status") -> "État : $value"
        else -> value
    }
}

private fun formatTimestampShort(isoString: String): String {
    return try {
        val trimmed = isoString.substringBefore(".")
        val parser = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.getDefault())
        val date = parser.parse(trimmed)
        val formatter = SimpleDateFormat("dd MMM, HH:mm", Locale.getDefault()) // ex: "04 Mar, 10:29"
        if (date != null) formatter.format(date) else "--:--"
    } catch (e: Exception) {
        "--:--"
    }
}
