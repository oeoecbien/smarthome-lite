package com.example.smarthome

import android.R
import androidx.compose.animation.Crossfade
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.compose.foundation.gestures.detectVerticalDragGestures
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
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
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.smarthome.ui.theme.SmartHomeTheme
import com.example.smarthome.ui.theme.*
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.compose.material.icons.filled.Visibility
import androidx.compose.material.icons.filled.VisibilityOff
import androidx.compose.material.icons.materialIcon
import androidx.compose.material.icons.outlined.ExitToApp
import androidx.compose.material.icons.outlined.Notifications
import androidx.compose.material.icons.outlined.WbSunny
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.darkColorScheme
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.input.pointer.pointerInput

import androidx.compose.ui.tooling.preview.Preview

import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Lightbulb
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.graphics.SolidColor


class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            var isDarkTheme by rememberSaveable { mutableStateOf(false) }

            SmartHomeTheme(darkTheme = isDarkTheme, dynamicColor = false) {
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

@Composable
fun SmartHomeApp(
    viewModel: SmartHomeViewModel,
    isDarkTheme: Boolean,
    onThemeChange: (Boolean) -> Unit
) {
    var currentDestination by rememberSaveable { mutableStateOf(AppDestinations.HOME) }

    NavigationSuiteScaffold(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background),
        navigationSuiteItems = {
            AppDestinations.entries.forEach {
                item(
                    icon = { Icon(it.icon, contentDescription = it.label) },
                    label = { Text(it.label) },
                    selected = it == currentDestination,
                    onClick = { currentDestination = it }
                )
            }
        }
    ) {
        Scaffold(
            modifier = Modifier.fillMaxSize(),
            containerColor = MaterialTheme.colorScheme.background
        ) { innerPadding ->
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background(MaterialTheme.colorScheme.background)
                    .padding(innerPadding)
            ) {
                when (currentDestination) {
                    // On passe le viewModel à HomeScreen pour qu'il affiche les données chargées
                    AppDestinations.HOME -> HomeScreen(viewModel = viewModel)
                    AppDestinations.FAVORITES -> FavoritesScreen()
                    AppDestinations.PROFILE -> ProfileScreen(
                        name = viewModel.currentUsername,
                        email = viewModel.currentEmail,
                        onLogoutClick = { viewModel.logout() },
                        isDarkTheme = isDarkTheme,
                        onThemeChange = onThemeChange
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

/*
// Page Home
@Composable
fun HomeScreen(modifier: Modifier = Modifier, viewModel: SmartHomeViewModel = viewModel()) {
    // On observe les données du ViewModel
    val lamps by viewModel.lamps
    val error by viewModel.errorMessage

    var selectedLampId by remember { mutableStateOf<Int?>(null) }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(backgroundColor)
    ) {
        Crossfade(targetState = selectedLampId, label = "PageTransition") { lampId ->
            if (lampId == null) {
                Column(modifier = modifier
                    .fillMaxSize()
                    .padding(16.dp)) {
                    Row(
                        horizontalArrangement = Arrangement.SpaceBetween,
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Text(
                            text = "Bonjour ${viewModel.currentUsername},",
                            style = MaterialTheme.typography.headlineMedium,
                            fontWeight = FontWeight.Bold
                        )

                        Button(
                            onClick = {
                                viewModel.loadData(
                                    viewModel.currentUsername,
                                    viewModel.currentPassword
                                )
                            }) {
                            Icon(
                                imageVector = Icons.Default.Refresh,
                                contentDescription = null,
                            )
                        }
                    }

                    // Affichage d'erreur si besoin
                    if (error != null) {
                        Text(
                            text = error ?: "",
                            color = MaterialTheme.colorScheme.error,
                            modifier = Modifier.padding(vertical = 8.dp)
                        )
                    }

                    Text(
                        text = "Appareils détectés (${lamps.size})",
                        style = MaterialTheme.typography.bodyLarge,
                        color = Color.Gray,
                        modifier = Modifier.padding(bottom = 24.dp)
                    )

                    LazyVerticalGrid(
                        columns = GridCells.Fixed(2),
                        horizontalArrangement = Arrangement.spacedBy(12.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        items(lamps.size) { index ->
                            LampCard(
                                lamp = lamps[index],
                                onClick = { selectedLampId = lamps[index].id }
                            )
                        }
                    }
                }
            } else {
                // Vue Détails
                val activeLamp = lamps.find { it.id == lampId }
                if (activeLamp != null) {
                    LampControlScreen(
                        lamp = activeLamp,
                        onBack = { selectedLampId = null },
                        onUpdate = { updatedLamp ->
                            viewModel.updateLamp(updatedLamp)
                        }
                    )
                }
            }
        }
    }

}

*/
@Composable
fun LampCard(lamp: SmartLamp, onClick: () -> Unit) {
    Card(
        modifier = Modifier
            .height(160.dp)
            .clickable { onClick() },
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(
            containerColor = if (lamp.isOn) MaterialTheme.colorScheme.primaryContainer else MaterialTheme.colorScheme.surfaceVariant
        )
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(16.dp),
            verticalArrangement = Arrangement.SpaceBetween
        ) {
            Box(
                modifier = Modifier
                    .size(40.dp)
                    .clip(CircleShape)
                    .background(Color.White.copy(alpha = 0.5f)),
                contentAlignment = Alignment.Center
            ) {
                // Utilisation d'une icône standard pour éviter les erreurs de dépendances
                Icon(
                    imageVector = Icons.Filled.Lightbulb, // Tu peux mettre Icons.Filled.Lightbulb si tu as la lib extended
                    contentDescription = "Lampe",
                    tint = MaterialTheme.colorScheme.onSurface
                )
            }

            Column {
                Text(
                    text = lamp.name,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    text = if (lamp.isOn) "Allumée • ${(lamp.brightness * 100).toInt()}%" else "Éteinte",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}

@Composable
fun LampControlScreen(
    lamp: SmartLamp,
    onBack: () -> Unit,
    onUpdate: (SmartLamp) -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .padding(20.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // 1. HEADER (Titre + Status)
        LampHeader(name = lamp.name, onBack = onBack)

        Spacer(modifier = Modifier.height(30.dp))

        // 2. POWER CARD (L'interrupteur)
        PowerControlCard(
            isOn = lamp.isOn,
            onToggle = { isChecked ->
                onUpdate(lamp.copy(isOn = isChecked))
            }
        )

        Spacer(modifier = Modifier.height(40.dp))

        // 3. POURCENTAGE TEXTE
        Text(
            text = "${(lamp.brightness * 100).toInt()}%",
            color = Color.White,
            fontSize = 48.sp,
            fontWeight = FontWeight.Bold
        )

        Spacer(modifier = Modifier.height(16.dp))

        // 4. ICONE SOLEIL
        Icon(
            imageVector = Icons.Outlined.WbSunny,
            contentDescription = "Brightness",
            tint = Color.Gray,
            modifier = Modifier.size(28.dp)
        )

        Spacer(modifier = Modifier.height(24.dp))

        // 5. SLIDER VERTICAL PERSONNALISÉ (Le gros morceau)
        // On ne l'affiche que si la lampe est allumée pour l'effet visuel,
        // ou on le grise si éteint.
        VerticalNeonSlider(
            brightness = lamp.brightness,
            isEnabled = lamp.isOn,
            onBrightnessChange = { newBrightness ->
                // On met à jour la lampe (note: onUpdate gère déjà le debounce grâce au ViewModel)
                onUpdate(lamp.copy(brightness = newBrightness, isOn = true))
            }
        )
    }
}

// --- SOUS-COMPOSANTS ---

@Composable
fun LampHeader(name: String, onBack: () -> Unit) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        // Bouton Retour
        IconButton(onClick = onBack) {
            Icon(Icons.Default.ArrowBack, contentDescription = "Back", tint = MaterialTheme.colorScheme.primary)
        }

        // Titre et Status
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Text(
                text = name,
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.primary
            )
            Row(verticalAlignment = Alignment.CenterVertically) {
                // Petit point vert
                Box(
                    modifier = Modifier
                        .size(6.dp)
                        .clip(CircleShape)
                        .background(TextGreen)
                )
                Spacer(modifier = Modifier.width(6.dp))
                Text(
                    text = "Online",
                    style = MaterialTheme.typography.bodySmall,
                    color = TextGreen
                )
            }
        }

        // Bouton Settings
        IconButton(onClick = { /* Todo: Settings */ }) {
            Icon(Icons.Default.Settings, contentDescription = "Settings", tint = MaterialTheme.colorScheme.primary)
        }
    }
}

@Composable
fun PowerControlCard(isOn: Boolean, onToggle: (Boolean) -> Unit) {
    Card(
        shape = RoundedCornerShape(24.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.tertiary),
        modifier = Modifier.fillMaxWidth().height(80.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxSize().padding(horizontal = 20.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                // Icone Ampoule dans un cercle
                Box(
                    modifier = Modifier
                        .size(44.dp)
                        .clip(CircleShape)
                        .background(if (isOn) NeonBlue.copy(alpha = 0.2f) else Color.Gray.copy(alpha = 0.2f)),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        imageVector = Icons.Default.Lightbulb,
                        contentDescription = null,
                        tint = if (isOn) NeonBlue else Color.Gray
                    )
                }
                Spacer(modifier = Modifier.width(16.dp))

                // Textes
                Column {
                    Text(
                        text = "Power",
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.primary
                    )
                    Text(
                        text = if (isOn) "Allumer" else "Eteint",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.secondary
                    )
                }
            }

            // Switch personnalisé
            Switch(
                checked = isOn,
                onCheckedChange = onToggle,
                colors = SwitchDefaults.colors(
                    checkedThumbColor = Color.White,
                    checkedTrackColor = NeonBlue,
                    uncheckedThumbColor = Color.Gray,
                    uncheckedTrackColor = DarkSurface
                )
            )
        }
    }
}

@Composable
fun VerticalNeonSlider(
    brightness: Float,
    isEnabled: Boolean,
    onBrightnessChange: (Float) -> Unit
) {
    // Hauteur totale du slider
    val barHeight = 300.dp
    val barWidth = 60.dp

    // Pour gérer le Drag (glissement) manuellement
    // BoxWithConstraints nous permet de connaître la hauteur en pixels pour les calculs
    BoxWithConstraints(
        modifier = Modifier
            .height(barHeight)
            .width(barWidth),
        contentAlignment = Alignment.BottomCenter
    ) {
        val maxHeightPx = constraints.maxHeight.toFloat()

        // --- 1. LE FOND (Track sombre) ---
        Box(
            modifier = Modifier
                .fillMaxSize()
                .clip(RoundedCornerShape(40.dp))
                .background(CardSurface)
                .border(1.dp, Color.White.copy(alpha = 0.1f), RoundedCornerShape(40.dp))
        )

        // --- 2. LA BARRE REMPLIE (Bleu Néon) ---
        // On calcule la hauteur de la barre bleue en fonction de la luminosité
        val fillHeight = maxHeightPx * brightness

        // Dégradé pour l'effet "Glow"
        val neonBrush = Brush.verticalGradient(
            colors = listOf(NeonBlueGlow, NeonBlue)
        )

        Box(
            modifier = Modifier
                .fillMaxWidth()
                // Conversion de la hauteur calculée (pixels) en DP
                .height(with(androidx.compose.ui.platform.LocalDensity.current) { fillHeight.toDp() })
                .clip(RoundedCornerShape(bottomStart = 40.dp, bottomEnd = 40.dp, topStart = 10.dp, topEnd = 10.dp))
                // CORRECTION ICI :
                .background(
                    if (isEnabled) neonBrush else SolidColor(Color.Gray)
                )
        )

        // --- 3. LE ROND (Thumb) ---
        // On le positionne dynamiquement
        Box(
            modifier = Modifier
                .offset(y = -with(androidx.compose.ui.platform.LocalDensity.current) { fillHeight.toDp() - (barWidth/2) }) // Centrer le rond sur le haut de la barre
                .size(barWidth - 10.dp) // Un peu plus petit que la largeur totale
                .clip(CircleShape)
                .background(Color.White)
                .shadow(10.dp, CircleShape, spotColor = NeonBlue) // L'ombre bleue
        ) {
            // Petit point au centre du rond blanc (optionnel, pour le style)
            Box(
                modifier = Modifier
                    .size(6.dp)
                    .clip(CircleShape)
                    .background(Color.LightGray)
                    .align(Alignment.Center)
            )
        }

        // --- 4. GESTION DU TOUCHER (Invisible, par dessus tout) ---
        Box(
            modifier = Modifier
                .fillMaxSize()
                .clip(RoundedCornerShape(40.dp))
                .pointerInput(Unit) {
                    detectVerticalDragGestures(
                        onDragStart = { offset ->
                            // Gère le clic initial (saut direct à la position)
                            val newBrightness = ((maxHeightPx - offset.y) / maxHeightPx).coerceIn(0f, 1f)
                            if (isEnabled) onBrightnessChange(newBrightness)
                        },
                        onVerticalDrag = { change, _ -> // CORRECTION : "onVerticalDrag" au lieu de "onDrag"
                            change.consume() // Important : on consomme l'événement

                            // Gère le glissement
                            val newBrightness = ((maxHeightPx - change.position.y) / maxHeightPx).coerceIn(0f, 1f)
                            if (isEnabled) onBrightnessChange(newBrightness)
                        }
                    )
                }
        )
    }
}


@Composable
fun FavoritesScreen(modifier: Modifier = Modifier) {
    Box(modifier = modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        Text(text = "Tes favoris")
    }
}


@Composable
fun LoginScreen(viewModel: SmartHomeViewModel) {
    // Variables locales pour les champs de texte
    var username by remember { mutableStateOf("admin") } // Pré-rempli pour tester vite
    var password by remember { mutableStateOf("admin123") }
    var passwordVisible by remember { mutableStateOf(false) }

    val isLoading by viewModel.isLoading
    val error by viewModel.errorMessage

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(
                Brush.verticalGradient(
                    colors = listOf(
                        Color(0xFF0A1A33),
                        Color(0xFF060B16)
                    )
                )
            ),
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 24.dp)
                .align(Alignment.Center),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Spacer(modifier = Modifier.height(24.dp))

            // Icon container
            Box(
                modifier = Modifier
                    .size(72.dp)
                    .clip(RoundedCornerShape(16.dp))
                    .background(Color(0xFF121826)),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = Icons.Filled.Lightbulb,
                    contentDescription = null,
                    tint = Color(0xFF2979FF),
                    modifier = Modifier.size(32.dp)
                )
            }

            Spacer(modifier = Modifier.height(32.dp))

            Text(
                text = "SmartHome",
                color = Color.White,
                fontSize = 28.sp,
                fontWeight = FontWeight.Bold
            )

            Spacer(modifier = Modifier.height(8.dp))

            Text(
                text = "Connecter vous pour accéder à vos appareils",
                color = Color(0xFF9AA4B2),
                fontSize = 14.sp
            )

            Spacer(modifier = Modifier.height(32.dp))

            // Username
            OutlinedTextField(
                value = username,
                onValueChange = { username = it },
                label = { Text("Utilisateur") },
                singleLine = true,
                leadingIcon = {
                    Icon(Icons.Default.Person, contentDescription = null)
                },
                modifier = Modifier.fillMaxWidth(),
                colors = darkTextFieldColors()
            )

            Spacer(modifier = Modifier.height(16.dp))

            // Champ Password
            OutlinedTextField(
                value = password,
                onValueChange = { password = it },
                label = { Text("Mot de passe") },
                leadingIcon = {
                    Icon(Icons.Default.Lock, contentDescription = null)
                },
                trailingIcon = {
                    IconButton(onClick = { passwordVisible = !passwordVisible }) {
                        Icon(
                            imageVector = if (passwordVisible)
                                Icons.Filled.Visibility
                            else
                                Icons.Filled.VisibilityOff,
                            contentDescription = null
                        )
                    }
                },
                visualTransformation = if (passwordVisible)
                    VisualTransformation.None
                else
                    PasswordVisualTransformation(),
                modifier = Modifier.fillMaxWidth(),
                colors = darkTextFieldColors()
            )

            Spacer(modifier = Modifier.height(24.dp))

            // Message d'erreur (si existe)
            if (error != null) {
                Text(
                    text = error ?: "",
                    color = MaterialTheme.colorScheme.error,
                    modifier = Modifier.padding(bottom = 16.dp)
                )
            }

            // Bouton de connexion
            Button(
                onClick = { viewModel.login(username, password) },
                enabled = !isLoading,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(52.dp),
                shape = RoundedCornerShape(14.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color(0xFF2979FF)
                )

            ) {
                if (isLoading) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(24.dp),
                        color = MaterialTheme.colorScheme.onPrimary
                    )
                } else {
                    Text("Se connecter")
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            Button(
                onClick = { /* TODO */ },
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color.Transparent,


                )

            ) {
                Text(
                    text = "Mot de passe oublié ?",
                    fontSize = 14.sp,
                    color = TextWhite
                )
            }
            Spacer(modifier = Modifier.height(32.dp))
        }
    }
}



@Composable
fun ProfileScreen(
    name: String,
    email: String,
    onLogoutClick: () -> Unit,
    isDarkTheme: Boolean,
    onThemeChange: (Boolean) -> Unit,
    modifier: Modifier = Modifier
) {
    LazyColumn(
        modifier = modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background),
        horizontalAlignment = Alignment.CenterHorizontally,
        contentPadding = PaddingValues(24.dp)
    ) {

        // --- 1. Header ---
        item {
            Text(
                text = "Profil",
                style = MaterialTheme.typography.titleLarge,
                color = MaterialTheme.colorScheme.primary,
                fontWeight = FontWeight.Bold,
                modifier = Modifier.padding(bottom = 32.dp)
            )
        }

        // --- 2. Avatar Section ---
        item {
            Box(
                contentAlignment = Alignment.BottomEnd,
                modifier = Modifier.size(120.dp)
            ) {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .clip(CircleShape)
                        .background(Color(0xFFE0E0E0)),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        imageVector = Icons.Default.Person,
                        contentDescription = null,
                        modifier = Modifier.size(80.dp),
                        tint = Color.Gray
                    )
                }

                Box(
                    modifier = Modifier
                        .size(36.dp)
                        .clip(CircleShape)
                        .background(PrimaryBlue)
                        .border(3.dp, MaterialTheme.colorScheme.background, CircleShape)
                        .clickable { },
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        imageVector = Icons.Default.CameraAlt,
                        contentDescription = "Change photo",
                        tint = Color.White,
                        modifier = Modifier.size(18.dp)
                    )
                }
            }
        }

        item { Spacer(modifier = Modifier.height(16.dp)) }

        // --- 3. User Info ---
        item {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    text = name.ifEmpty { "Utilisateur" },
                    style = MaterialTheme.typography.headlineSmall,
                    color = MaterialTheme.colorScheme.primary,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.width(8.dp))
                Icon(
                    imageVector = Icons.Default.Edit,
                    contentDescription = "Edit name",
                    tint = PrimaryBlue,
                    modifier = Modifier
                        .size(20.dp)
                        .clickable { }
                )
            }
        }

        item {
            Text(
                text = email,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.primary
            )
        }

        item { Spacer(modifier = Modifier.height(40.dp)) }

        // --- 4. Settings Menu ---
        item {
            Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {

                ProfileMenuItem(
                    icon = if (isDarkTheme) Icons.Default.DarkMode else Icons.Default.LightMode,
                    title = "Thème de l'application",
                    subtitle = if (isDarkTheme) "Mode Sombre" else "Mode Clair",
                    iconBgColor = if (isDarkTheme) Color(0xFF1E1F2B) else Color(0xFFF5F5F5),
                    iconColor = if (isDarkTheme) Color.White else Color.Black,
                    trailingContent = {
                        Switch(
                            checked = isDarkTheme,
                            onCheckedChange = onThemeChange
                        )
                    }
                )

                ProfileMenuItem(
                    icon = Icons.Default.Lock,
                    title = "Account Security",
                    subtitle = "Password, 2FA",
                    iconBgColor = PrimaryBlue.copy(alpha = 0.1f),
                    iconColor = PrimaryBlue
                )

                ProfileMenuItem(
                    icon = Icons.Default.Notifications,
                    title = "Notification Preferences",
                    subtitle = "Push, Email, SMS",
                    iconBgColor = AccentOrange.copy(alpha = 0.1f),
                    iconColor = AccentOrange
                )

                ProfileMenuItem(
                    icon = Icons.Default.Code,
                    title = "API Configuration",
                    subtitle = "Keys & Webhooks",
                    iconBgColor = AccentPurple.copy(alpha = 0.1f),
                    iconColor = AccentPurple
                )
            }
        }

        item { Spacer(modifier = Modifier.height(32.dp)) }

        // --- 5. Logout Button ---
        item {
            Button(
                onClick = onLogoutClick,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(56.dp),
                shape = RoundedCornerShape(16.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = MaterialTheme.colorScheme.tertiary,
                    contentColor = DangerRed
                )
            ) {
                Icon(
                    imageVector = Icons.Outlined.ExitToApp,
                    contentDescription = null,
                    modifier = Modifier.size(20.dp)
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = "Log Out",
                    fontSize = 16.sp,
                    fontWeight = FontWeight.SemiBold
                )
            }
        }

        item { Spacer(modifier = Modifier.height(20.dp)) }
    }

}

// --- Composant réutilisable pour les lignes de menu ---
@Composable
fun ProfileMenuItem(
    icon: ImageVector,
    title: String,
    subtitle: String,
    iconBgColor: Color,
    iconColor: Color,
    trailingContent: @Composable (() -> Unit)? = null
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .height(80.dp)
            .clip(RoundedCornerShape(20.dp))
            .background(MaterialTheme.colorScheme.tertiary)
            .clickable { }
            .padding(horizontal = 16.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        // Icon Box
        Box(
            modifier = Modifier
                .size(48.dp)
                .clip(RoundedCornerShape(12.dp))
                .background(iconBgColor),
            contentAlignment = Alignment.Center
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = iconColor
            )
        }

        Spacer(modifier = Modifier.width(16.dp))

        // Texts
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = title,
                color = MaterialTheme.colorScheme.primary,
                fontWeight = FontWeight.SemiBold,
                fontSize = 16.sp
            )
            Text(
                text = subtitle,
                color = MaterialTheme.colorScheme.secondary,
                fontSize = 12.sp
            )
        }

        // Action or Arrow
        if (trailingContent != null) {
            trailingContent()
        } else {
            Icon(
                imageVector = Icons.Default.ChevronRight,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.primary
            )
        }
    }
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
    viewModel: SmartHomeViewModel = viewModel()
) {
    val lamps by viewModel.lamps
    val error by viewModel.errorMessage
    var selectedLampId by remember { mutableStateOf<Int?>(null) }

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

                /*
                Spacer(modifier = Modifier.height(20.dp))

                // 2. Status Chips (3 Lights On, Temp, etc.)
                StatusChipsSection()

                 */

                Spacer(modifier = Modifier.height(24.dp))

                /*
                // 3. Section Scènes
                Text(
                    text = "Mes scènes",
                    style = MaterialTheme.typography.titleLarge,
                    color = MaterialTheme.colorScheme.primary,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.height(16.dp))

                ScenesRow()

                Spacer(modifier = Modifier.height(24.dp))
                 */

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
                    lamps = lamps,
                    onLampClick = { selectedLampId = it.id },
                    onToggleLamp = { lamp, newState ->
                        viewModel.updateLamp(lamp.copy(isOn = newState))
                    }
                )
            }
        } else {
            // --- VUE DÉTAIL (Code précédent) ---
            val activeLamp = lamps.find { it.id == lampId }
            if (activeLamp != null) {
                LampControlScreen(
                    lamp = activeLamp,
                    onBack = { selectedLampId = null },
                    onUpdate = { viewModel.updateLamp(it) }
                )
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
    lamps: List<SmartLamp>,
    onLampClick: (SmartLamp) -> Unit,
    onToggleLamp: (SmartLamp, Boolean) -> Unit
) {
    LazyVerticalGrid(
        columns = GridCells.Fixed(2),
        horizontalArrangement = Arrangement.spacedBy(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
        modifier = Modifier.height(400.dp) // Hauteur fixe ou weight(1f)
    ) {
        // --- LAMPES (Depuis l'API) ---
        items(lamps.size) { index ->
            val lamp = lamps[index]
            DeviceCard(
                name = lamp.name,
                status = if (lamp.isOn) "On • ${(lamp.brightness * 100).toInt()}%" else "Off",
                isOn = lamp.isOn,
                icon = Icons.Default.Lightbulb, // Tu peux varier selon le nom
                onClick = { onLampClick(lamp) },
                onToggle = { onToggleLamp(lamp, it) }
            )
        }

        // --- THERMOSTAT (Fictif, prend 2 colonnes) ---
        item(span = { GridItemSpan(2) }) {
            ThermostatCard()
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

@Preview(showBackground = true)
@Composable
fun ThermostatCard() {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .height(80.dp)
            .clip(RoundedCornerShape(24.dp))
            .background(MaterialTheme.colorScheme.tertiary)
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
                Text("Thermostat", color = MaterialTheme.colorScheme.primary, fontWeight = FontWeight.Bold)
                Text("Heating to 23°C", color = MaterialTheme.colorScheme.secondary, fontSize = 12.sp)
            }
        }

        Row(verticalAlignment = Alignment.CenterVertically) {
            IconButton(onClick = {}) { Icon(Icons.Default.Remove, null, tint = MaterialTheme.colorScheme.primary) } // Utilise une icône '-'
            Text("21°", color = MaterialTheme.colorScheme.primary, fontSize = 22.sp, fontWeight = FontWeight.Bold)
            IconButton(onClick = {}) { Icon(Icons.Default.Add, null, tint = MaterialTheme.colorScheme.primary) }
        }
    }
}



// Extension pour le scale du switch
fun Modifier.scale(scale: Float): Modifier = this.then(
    androidx.compose.ui.Modifier.graphicsLayer(scaleX = scale, scaleY = scale)
)