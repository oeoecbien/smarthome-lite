package com.example.smarthome.ui.screens

import com.example.smarthome.data.model.*
import com.example.smarthome.data.api.*
import com.example.smarthome.ui.viewmodel.*

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.BatteryFull
import androidx.compose.material.icons.filled.DirectionsRun
import androidx.compose.material.icons.filled.Opacity
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.Thermostat
import androidx.compose.material.icons.filled.WbSunny
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.smarthome.ui.theme.AccentOrange
import com.example.smarthome.ui.theme.NeonBlue

@Composable
fun SensorControlScreen(
    sensor: SmartSensor,
    onBack: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background) // Dark background
            .verticalScroll(rememberScrollState())
            .padding(20.dp)
    ) {


        Spacer(modifier = Modifier.height(20.dp))

        // --- Grid of Sensors ---
        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(16.dp)) {
            // Column 1
            Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(16.dp)) {
                SensorDetailCard(
                    icon = Icons.Default.Thermostat,
                    iconColor = AccentOrange,
                    label = "TEMP",
                    value = "${sensor.temperature}",
                    unit = "°C",
                    subText = "Normal" // Placeholder logic
                )
                SensorDetailCard(
                    icon = Icons.Default.WbSunny,
                    iconColor = Color.Yellow,
                    label = "LIGHT",
                    value = "${sensor.illuminance}",
                    unit = " Lux",
                    subText = "Natural Light"
                )
                SensorDetailCard(
                    icon = Icons.Default.WbSunny, // UV Placeholder
                    iconColor = Color(0xFFE91E63), // Pink for UV
                    label = "UV INDEX",
                    value = "0",
                    unit = "",
                    subText = "Low"
                )
            }

            // Column 2
            Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(16.dp)) {
                SensorDetailCard(
                    icon = Icons.Default.Opacity,
                    iconColor = NeonBlue,
                    label = "HUMIDITY",
                    value = "${sensor.humidity}",
                    unit = "%",
                    subText = "Optimal Range"
                )
                SensorDetailCard(
                    icon = Icons.Filled.DirectionsRun, // Vibration Placeholder
                    iconColor = Color.Magenta,
                    label = "VIBRATION",
                    value = "None",
                    unit = "",
                    subText = "Stable Surface"
                )
                SensorDetailCard(
                    icon = Icons.Default.BatteryFull,
                    iconColor = Color.Green,
                    label = "BATTERY",
                    value = "${sensor.battery}",
                    unit = "%",
                    subText = "Status: Excellent"
                )
            }
        }
    }
}

@Composable
fun MotionStatusCard(isActive: Boolean) {
    Card(
        shape = RoundedCornerShape(24.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF2A2A2A)),
        modifier = Modifier.fillMaxWidth().height(100.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxSize().padding(20.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(50.dp)
                    .clip(RoundedCornerShape(12.dp))
                    .background(NeonBlue),
                contentAlignment = Alignment.Center
            ) {
                Icon(Icons.Filled.DirectionsRun, contentDescription = null, tint = Color.White)
            }
            Spacer(modifier = Modifier.width(16.dp))
            Column {
                Text("MOTION STATUS", color = Color.Gray, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                Text(
                    if (isActive) "Active" else "Inactive",
                    color = if (isActive) NeonBlue else Color.Gray,
                    fontSize = 24.sp,
                    fontWeight = FontWeight.Bold
                )
            }
            Spacer(modifier = Modifier.weight(1f))
            if (isActive) {
                Box(
                    modifier = Modifier
                        .clip(RoundedCornerShape(50))
                        .background(NeonBlue.copy(alpha = 0.2f))
                        .padding(horizontal = 12.dp, vertical = 6.dp)
                ) {
                    Text("Live", color = NeonBlue, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                }
            }
        }
    }
}

@Composable
fun SensorDetailCard(
    icon: ImageVector,
    iconColor: Color,
    label: String,
    value: String,
    unit: String,
    subText: String
) {
    Card(
        shape = RoundedCornerShape(24.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.tertiary),
        modifier = Modifier.fillMaxWidth().height(160.dp)
    ) {
        Column(
            modifier = Modifier.fillMaxSize().padding(16.dp),
            verticalArrangement = Arrangement.SpaceBetween
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Box(
                    modifier = Modifier
                        .size(40.dp)
                        .clip(CircleShape)
                        .background(Color(0xFF1E1E1E)),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(icon, contentDescription = null, tint = iconColor, modifier = Modifier.size(20.dp))
                }
                Text(label, color = Color.Gray, fontSize = 10.sp, fontWeight = FontWeight.Bold)
            }

            Column {
                Row(verticalAlignment = Alignment.Bottom) {
                    Text(value, color = MaterialTheme.colorScheme.primary, fontSize = 32.sp, fontWeight = FontWeight.Bold)
                    Text(unit, color = Color.Gray, fontSize = 16.sp, modifier = Modifier.padding(bottom = 6.dp))
                }
                Text(subText, color = Color.Gray, fontSize = 12.sp)
            }
        }
    }
}
