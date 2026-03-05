package com.example.smarthome.ui.components


import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.GridItemSpan
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ExitToApp
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.Notifications
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.res.painterResource
import com.example.smarthome.data.model.*
import com.example.smarthome.ui.theme.*
import com.example.smarthome.R




@Composable
fun HeaderSection(name: String) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(top = 16.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            // Avatar (Placeholder)
            Box(
                modifier = Modifier
                    .size(50.dp)
                    .clip(CircleShape)
                    .background(Color(0xFFFFCC80)), // Couleur peau
                contentAlignment = Alignment.Center
            ) {
                Icon(Icons.Default.Person, contentDescription = null, tint = Color.White)
            }
            Spacer(modifier = Modifier.width(12.dp))
            Column {
                Text("Bonjour,", color = MaterialTheme.colorScheme.secondary, fontSize = 14.sp)
                Text(name, color = MaterialTheme.colorScheme.primary, fontSize = 20.sp, fontWeight = FontWeight.Bold)
            }
        }
        // Cloche Notification
        IconButton(
            onClick = {},
            modifier = Modifier
                .size(45.dp)
                .clip(CircleShape)
                .background(CardBackground)
        ) {
            Icon(Icons.Outlined.Notifications, contentDescription = "Alerts", tint = TextWhite)
        }
    }
}

@Composable
fun StatusChipsSection() {
    LazyRow(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
        item {
            StatusChip(
                icon = Icons.Default.Lightbulb,
                label = "3 Lights On",
                color = PrimaryBlue, // Bleu actif
                textColor = Color.White
            )
        }
        item {
            StatusChip(
                icon = Icons.Default.Thermostat, // Icône température par défaut
                label = "21.5°C Avg",
                color = CardBackground,
                textColor = TextWhite
            )
        }
        item {
            StatusChip(
                icon = Icons.Default.Security,
                label = "System Safe",
                color = CardBackground,
                textColor = TextWhite
            )
        }
    }
}

@Composable
fun StatusChip(icon: ImageVector, label: String, color: Color, textColor: Color) {
    Row(
        modifier = Modifier
            .clip(RoundedCornerShape(30.dp))
            .background(color)
            .padding(horizontal = 16.dp, vertical = 12.dp),
            verticalAlignment = Alignment.CenterVertically
    ) {
        Icon(icon, contentDescription = null, tint = textColor, modifier = Modifier.size(18.dp))
        Spacer(modifier = Modifier.width(8.dp))
        Text(label, color = textColor, fontWeight = FontWeight.Medium)
    }
}

@Composable
fun ScenesRow() {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        SceneCard("Home", Icons.Default.Home, PrimaryBlue)
        SceneCard("Away", Icons.AutoMirrored.Outlined.ExitToApp, MaterialTheme.colorScheme.tertiary)
        SceneCard("Movie", Icons.Default.PlayArrow, MaterialTheme.colorScheme.tertiary)
    }
}

@Composable
fun SceneCard(name: String, icon: ImageVector, backgroundColor: Color) {
    Column(
        modifier = Modifier
            .width(100.dp)
            .height(100.dp)
            .clip(RoundedCornerShape(20.dp))
            .background(backgroundColor)
            .clickable { },
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Icon(icon, contentDescription = name, tint = MaterialTheme.colorScheme.primary, modifier = Modifier.size(32.dp))
        Spacer(modifier = Modifier.height(8.dp))
        Text(name, color = MaterialTheme.colorScheme.primary, fontWeight = FontWeight.Medium)
    }
}

@Composable
fun DeviceGrid(
    devices: List<SmartDevice>,
    onLampClick: (SmartLight) -> Unit,
    onSensorClick: (SmartSensor) -> Unit,
    onToggleLamp: (SmartLight, Boolean) -> Unit
) {
    LazyVerticalGrid(
        columns = GridCells.Fixed(2),
        horizontalArrangement = Arrangement.spacedBy(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
        modifier = Modifier.fillMaxHeight()
    ) {
        // --- LAMPES & CAPTEURS (Depuis l'API) ---
        items(devices.size, span = { index ->
            val device = devices[index]
            if (device is SmartSensor) {
                GridItemSpan(2) // Le thermostat prend toute la largeur
            } else {
                GridItemSpan(1)
            }
        }) { index ->
            val device = devices[index]

            when (device) {
                is SmartSensor -> {
                     ThermostatCard(
                        sensor = device,
                        onClick = { onSensorClick(device) }
                     )
                }
                is SmartLight -> {
                    DeviceCard(
                        name = device.name,
                        status = if (device.isOn) "On • ${(device.brightness * 100).toInt()}%" else "Off",
                        isOn = device.isOn,
                        icon = Icons.Default.Lightbulb, // Tu peux varier selon le nom
                        onClick = { onLampClick(device) },
                        onToggle = { onToggleLamp(device, it) }
                    )
                }
            }
        }
    }
}


@Composable
fun DeviceCard(
    name: String,
    status: String,
    isOn: Boolean,
    icon: ImageVector,
    onClick: () -> Unit,
    onToggle: (Boolean) -> Unit
) {

    // Dégradé bleu subtil si actif
    val modifierBackground = if (isOn) {
        Modifier.background(
            brush = Brush.verticalGradient(
                colors = listOf(PrimaryBlue.copy(alpha = 0.4f), PrimaryBlue.copy(alpha = 0.1f))
            )
        )
    } else {
        Modifier.background(MaterialTheme.colorScheme.tertiary)
    }

    Column(
        modifier = Modifier
            .aspectRatio(1f) // Carré
            .clip(RoundedCornerShape(24.dp))
            .then(modifierBackground)
            .clickable { onClick() }
            .padding(16.dp),
        verticalArrangement = Arrangement.SpaceBetween
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            // Icone dans un cercle
            Box(
                modifier = Modifier
                    .size(40.dp)
                    .clip(CircleShape)
                    .background(
                        if(isOn)
                            MaterialTheme.colorScheme.primary
                        else
                            MaterialTheme.colorScheme.secondary),
                contentAlignment = Alignment.Center
            ) {
                Icon(icon, contentDescription = null, tint = if(isOn) PrimaryBlue else MaterialTheme.colorScheme.primary)
            }

            // Switch personnalisé
            Switch(
                checked = isOn,
                onCheckedChange = onToggle,
                colors = SwitchDefaults.colors(
                    checkedThumbColor = TextWhite,
                    checkedTrackColor = PrimaryBlue,
                    uncheckedThumbColor = MaterialTheme.colorScheme.primary,
                    uncheckedTrackColor = MaterialTheme.colorScheme.background
                ),
                modifier = Modifier.scale(0.8f) // Un peu plus petit
            )
        }

        Column {
            Text(name, color = MaterialTheme.colorScheme.primary, fontWeight = FontWeight.SemiBold, fontSize = 16.sp)
            Text(status, color = if(isOn) PrimaryBlue else MaterialTheme.colorScheme.primary, fontSize = 12.sp)
        }
    }
}

@Composable
fun ThermostatCard(
    sensor: SmartSensor,
    onClick: () -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .height(80.dp)
            .clip(RoundedCornerShape(24.dp))
            .background(MaterialTheme.colorScheme.tertiary)
            .clickable { onClick() }
            .padding(16.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(
                modifier = Modifier
                    .size(48.dp)
                    .clip(CircleShape), // Fond orange très sombre
                contentAlignment = Alignment.Center
            ) {
                Image(painter = painterResource(R.drawable.sensor_svg), contentDescription = null)
            }
            Spacer(modifier = Modifier.width(12.dp))
            Column {
                Text(sensor.name, color = MaterialTheme.colorScheme.primary, fontWeight = FontWeight.Bold)
                Text("Humidity: ${sensor.humidity}%", color = MaterialTheme.colorScheme.secondary, fontSize = 12.sp)
            }
        }

        Row(verticalAlignment = Alignment.CenterVertically) {
            // Affichage de la température
            Text("${sensor.temperature}°", color = MaterialTheme.colorScheme.primary, fontSize = 22.sp, fontWeight = FontWeight.Bold)
        }
    }
}

// Extension pour le scale du switch
fun Modifier.scale(scale: Float): Modifier = this.then(
    Modifier.graphicsLayer(scaleX = scale, scaleY = scale)
)
