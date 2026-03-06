package com.example.smarthome.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Router
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.Timeline
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.smarthome.data.model.SmartLight
import com.example.smarthome.ui.theme.NeonBlue

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LampSettingsScreen(
    lamp: SmartLight,
    onBack: () -> Unit
) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Paramètres de l'appareil", color = MaterialTheme.colorScheme.primary) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(
                            Icons.AutoMirrored.Filled.ArrowBack,
                            contentDescription = "Retour",
                            tint = MaterialTheme.colorScheme.primary
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = Color.Transparent)
            )
        },
        containerColor = MaterialTheme.colorScheme.background
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .padding(horizontal = 20.dp)
                .verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            LampSectionHeader("Informations Générales", Icons.Default.Info)
            SettingsCard {
                SettingsRow("ID de l'appareil", lamp.id.toString())
                SettingsRow("Nom", lamp.name)
                SettingsRow("Type", lamp.type)
                SettingsRow("État actuel", if (lamp.isOn) "Allumé" else "Éteint")
                SettingsRow("Luminosité", "${(lamp.brightness * 100).toInt()}%")
            }

            LampSectionHeader("Configuration Technique", Icons.Default.Settings)
            SettingsCard {
                SettingsRow("Pin GPIO", "18")
                SettingsRow("Emplacement", "Salon")
            }

            LampSectionHeader("Passerelle & Connectivité", Icons.Default.Router)
            SettingsCard {
                SettingsRow("Raspberry Pi", "RPi Salon")
                SettingsRow("Statut RPi", "En ligne", color = Color(0xFF4CAF50))
            }

            LampSectionHeader("Historique", Icons.Default.Timeline)
            SettingsCard {
                SettingsRow("Créé le", "15 janv. 2025, 10:30")
                SettingsRow("Mis à jour le", "15 janv. 2025, 14:30")
            }

            Spacer(modifier = Modifier.height(24.dp))
        }
    }
}

@Composable
fun LampSectionHeader(title: String, icon: ImageVector) {
    Row(
        verticalAlignment = Alignment.CenterVertically,
        modifier = Modifier.padding(top = 8.dp)
    ) {
        Icon(icon, contentDescription = null, tint = NeonBlue, modifier = Modifier.size(20.dp))
        Spacer(modifier = Modifier.width(8.dp))
        Text(
            text = title,
            style = MaterialTheme.typography.titleSmall,
            color = Color.Gray,
            fontWeight = FontWeight.Bold
        )
    }
}

@Composable
fun SettingsCard(content: @Composable ColumnScope.() -> Unit) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.tertiary)
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
            content = content
        )
    }
}

@Composable
fun SettingsRow(label: String, value: String, color: Color = MaterialTheme.colorScheme.primary) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(text = label, style = MaterialTheme.typography.bodyMedium, color = Color.Gray)
        Text(text = value, style = MaterialTheme.typography.bodyLarge, color = color, fontWeight = FontWeight.Medium)
    }
}
