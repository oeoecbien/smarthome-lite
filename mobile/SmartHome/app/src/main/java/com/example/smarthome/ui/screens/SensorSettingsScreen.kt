package com.example.smarthome.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Router
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.smarthome.data.model.SmartSensor
import com.example.smarthome.ui.theme.NeonBlue

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SensorSettingsScreen(
    sensor: SmartSensor,
    onBack: () -> Unit,
    onDelete: () -> Unit
) {
    var showDeleteDialog by remember { mutableStateOf(false) }

    if (showDeleteDialog) {
        AlertDialog(
            onDismissRequest = { showDeleteDialog = false },
            title = { Text("Supprimer le capteur", color = MaterialTheme.colorScheme.primary) },
            text = { Text("Êtes-vous sûr de vouloir supprimer ce capteur ? Cette action est irréversible.", color = MaterialTheme.colorScheme.primary) },
            confirmButton = {
                TextButton(onClick = {
                    showDeleteDialog = false
                    onDelete()
                }) {
                    Text("Supprimer", color = Color.Red)
                }
            },
            dismissButton = {
                TextButton(onClick = { showDeleteDialog = false }) {
                    Text("Annuler", color = Color.Gray)
                }
            },
            containerColor = MaterialTheme.colorScheme.tertiary
        )
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Paramètres du capteur", color = MaterialTheme.colorScheme.primary) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(
                            Icons.AutoMirrored.Filled.ArrowBack,
                            contentDescription = "Retour",
                            tint = MaterialTheme.colorScheme.primary
                        )
                    }
                },
                actions = {
                    IconButton(onClick = { showDeleteDialog = true }) {
                        Icon(
                            Icons.Default.Delete,
                            contentDescription = "Supprimer",
                            tint = Color.Red
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
            SensorSectionHeader("Informations Générales", Icons.Default.Info)
            SensorSettingsCard {
                SensorSettingsRow("Device ID", sensor.id.toString())
                SensorSettingsRow("Node ID", "5") // Placeholder based on example
                SensorSettingsRow("Nom", sensor.name)
                SensorSettingsRow("Type de device", "aeotec_multisensor7")
                SensorSettingsRow("Modèle", "ZWA024")
            }

            SensorSectionHeader("Mesures Actuelles", Icons.Default.Settings)
            SensorSettingsCard {
                SensorSettingsRow("Mouvement", if (sensor.motion) "Détecté" else "Aucun", color = if (sensor.motion) NeonBlue else MaterialTheme.colorScheme.primary)
                SensorSettingsRow("Température", "${sensor.temperature}°C")
                SensorSettingsRow("Humidité", "${sensor.humidity}%")
                SensorSettingsRow("Luminosité", "${sensor.illuminance} Lux")
                SensorSettingsRow("UV Index", "0")
                SensorSettingsRow("Batterie", "${sensor.battery}%", color = if (sensor.battery < 20) Color.Red else Color.Green)
            }

            SensorSectionHeader("Connectivité", Icons.Default.Router)
            SensorSettingsCard {
                SensorSettingsRow("Passerelle", "RPi Salon")
                SensorSettingsRow("Statut", "Connecté", color = Color.Green)
            }

            Spacer(modifier = Modifier.height(100.dp))

        }
    }
}

@Composable
fun SensorSectionHeader(title: String, icon: ImageVector) {
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
fun SensorSettingsCard(content: @Composable ColumnScope.() -> Unit) {
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
fun SensorSettingsRow(label: String, value: String, color: Color = MaterialTheme.colorScheme.primary) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(text = label, style = MaterialTheme.typography.bodyMedium, color = Color.Gray)
        Text(text = value, style = MaterialTheme.typography.bodyLarge, color = color, fontWeight = FontWeight.Medium)
    }
}
