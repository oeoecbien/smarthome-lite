package com.example.smarthome

import android.R
import androidx.compose.animation.Crossfade
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.compose.foundation.gestures.detectVerticalDragGestures
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.annotation.StringRes
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.GridItemSpan
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.Sort
import androidx.compose.material.icons.automirrored.outlined.ExitToApp
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Slider
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.adaptive.navigationsuite.NavigationSuiteScaffold
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.smarthome.ui.theme.SmartHomeTheme
import com.example.smarthome.ui.theme.*
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.compose.material.icons.outlined.Notifications
import androidx.compose.material3.SwitchDefaults
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.material.icons.filled.Lightbulb
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.*
import androidx.compose.material3.adaptive.navigationsuite.NavigationSuiteDefaults



class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            var isDarkTheme by remember { mutableStateOf(false) }


            SmartHomeTheme(dynamicColor = false) {
                // On instancie le ViewModel au niveau le plus haut
                val viewModel: SmartHomeViewModel = viewModel()

                // ROUTAGE PRINCIPAL
                if (viewModel.isLoggedIn) {
                    // Si connecté -> Affiche l'application complète
                    SmartHomeApp(viewModel, isDarkTheme, onThemeChange = { isDarkTheme = it })
                } else {
                    // Sinon -> Affiche l'écran de Login
                    LoginScreen(viewModel)
                }
            }
        }
    }
}
// Modifie SmartHomeApp pour accepter le viewModel déjà créé
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SmartHomeApp(
    viewModel: SmartHomeViewModel,
    isDarkTheme: Boolean,
    onThemeChange: (Boolean) -> Unit
) {
    var currentDestination by rememberSaveable { mutableStateOf(AppDestinations.HOME) }
    // Hoisted state for Lamp detail navigation
    var selectedLampId by rememberSaveable { mutableStateOf<Int?>(null) }
    // Observe lamps to get the name for the title
    val devices by viewModel.devices
    val snackbarHostState = remember { SnackbarHostState() }

    NavigationSuiteScaffold(
        containerColor = MaterialTheme.colorScheme.tertiary,
        navigationSuiteColors = NavigationSuiteDefaults.colors(
            navigationBarContainerColor = MaterialTheme.colorScheme.tertiary,
            navigationRailContainerColor = MaterialTheme.colorScheme.tertiary,
        ),
        navigationSuiteItems = {
            AppDestinations.entries.forEach { dest ->
                item(
                    icon = { Icon(dest.icon, contentDescription = dest.label) },
                    label = { Text(dest.label) },
                    selected = dest == currentDestination,
                    onClick = { currentDestination = dest }
                )
            }
        }
    ) {
        Scaffold(
            modifier = Modifier.fillMaxSize(),
            containerColor = MaterialTheme.colorScheme.tertiary,
            snackbarHost = { SnackbarHost(snackbarHostState) },

            topBar = {
                TopAppBar(
                    title = {
                        val titleText = if (selectedLampId != null) {
                            devices.find { it.id == selectedLampId }?.name ?: "Détail"
                        } else {
                            currentDestination.label
                        }
                        Text(text = titleText)
                    },
                    navigationIcon = {
                        if (selectedLampId != null) {
                            IconButton(onClick = { selectedLampId = null }) {
                                Icon(Icons.Default.ArrowBack, contentDescription = "Back", tint = MaterialTheme.colorScheme.primary)
                            }
                        }
                    },
                    colors = TopAppBarDefaults.topAppBarColors(
                        containerColor = MaterialTheme.colorScheme.background,
                        titleContentColor = MaterialTheme.colorScheme.primary,
                        navigationIconContentColor = MaterialTheme.colorScheme.primary,
                        actionIconContentColor = Color.White
                    )
                )
            }
        ) { innerPadding ->
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(innerPadding)
            ) {
                when (currentDestination) {
                    AppDestinations.HOME -> HomeScreen(
                        viewModel = viewModel,
                        selectedLampId = selectedLampId,
                        onLampSelect = { selectedLampId = it }
                    )
                    AppDestinations.FAVORITES -> FavoritesScreen()
                    AppDestinations.PROFILE -> ProfileScreen(
                        viewModel.currentUsername,
                        viewModel.currentEmail,
                        { viewModel.logout() },
                        isDarkTheme,
                        onThemeChange
                    )
                }
            }
        }
    }
}


enum class AppDestinations(val label: String, val icon: ImageVector) {
    HOME("Accueil", Icons.Default.Home),
    FAVORITES("Favoris", Icons.Default.Favorite),
    PROFILE("Profil", Icons.Default.AccountBox),
}

@Composable
fun darkTextFieldColors() = OutlinedTextFieldDefaults.colors(
    focusedBorderColor = Color(0xFF2979FF),
    unfocusedBorderColor = Color(0xFF2A3245),
    focusedTextColor = Color.White,
    unfocusedTextColor = Color.White,
    focusedLabelColor = Color(0xFF9AA4B2),
    unfocusedLabelColor = Color(0xFF9AA4B2),
    cursorColor = Color(0xFF2979FF),
    focusedLeadingIconColor = Color(0xFF9AA4B2),
    unfocusedLeadingIconColor = Color(0xFF9AA4B2),
    focusedTrailingIconColor = Color(0xFF9AA4B2),
    unfocusedTrailingIconColor = Color(0xFF9AA4B2)
)


@Composable
fun HomeScreen(
    modifier: Modifier = Modifier,
    viewModel: SmartHomeViewModel = viewModel(),
    selectedLampId: Int?,
    onLampSelect: (Int?) -> Unit
) {
    val devices by viewModel.devices
    val error by viewModel.errorMessage
    // Local state removed, using hoisted state passed via parameters

    // Navigation entre Liste et Détail
    Crossfade(targetState = selectedLampId, label = "PageTransition") { lampId ->
        if (lampId == null) {
            // --- VUE PRINCIPALE (Design de l'image) ---
            Column(
                modifier = modifier
                    .fillMaxSize()
                    .background(MaterialTheme.colorScheme.background) // Fond sombre global
                    .padding(horizontal = 20.dp)
            ) {
                // 1. En-tête (Profil + Notif)
                HeaderSection(name = "${viewModel.currentUsername},")

                Spacer(modifier = Modifier.height(24.dp))

                // 4. Section Devices (Grille)
                Text(
                    text = "Mes appareils",
                    style = MaterialTheme.typography.titleLarge,
                    color = MaterialTheme.colorScheme.primary,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.height(16.dp))

                // Grille intelligente
                DeviceGrid(
                    devices = devices,
                    onLampClick = { onLampSelect(it.id) },
                    onSensorClick = { onLampSelect(it.id) }, // Réutilise le même ID state
                    onToggleLamp = { lamp, newState ->
                         viewModel.updateDevice(lamp.copy(isOn = newState))
                    }
                )
            }
        } else {
            // --- VUE DÉTAIL ---
            val activeDevice = devices.find { it.id == lampId }
            if (activeDevice != null) {
                when (activeDevice) {
                    is SmartLight -> {
                        LampControlScreen(
                            lamp = activeDevice,
                            onBack = { onLampSelect(null) },
                            onUpdate = { viewModel.updateDevice(it) }
                        )
                    }
                    is SmartSensor -> {
                         SensorControlScreen(
                            sensor = activeDevice,
                            onBack = { onLampSelect(null) }
                        )
                    }
                }
            }
        }
    }
}

// --- SOUS-COMPOSANTS ---

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
                Text("Bonjour", color = MaterialTheme.colorScheme.secondary, fontSize = 14.sp)
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
        SceneCard("Away", Icons.Default.ExitToApp, MaterialTheme.colorScheme.tertiary)
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
        modifier = Modifier.height(400.dp) // Hauteur fixe ou weight(1f)
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
                    .clip(CircleShape)
                    .background(Color(0xFF2A2018)), // Fond orange très sombre
                contentAlignment = Alignment.Center
            ) {
                Icon(Icons.Default.Settings, contentDescription = null, tint = AccentOrange)
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
    androidx.compose.ui.Modifier.graphicsLayer(scaleX = scale, scaleY = scale)
)