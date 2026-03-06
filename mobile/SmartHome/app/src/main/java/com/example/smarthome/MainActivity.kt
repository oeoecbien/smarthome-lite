package com.example.smarthome

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.animation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.List
import androidx.compose.material.icons.filled.AccountBox
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.AutoAwesome
import androidx.compose.material.icons.filled.Notifications
import androidx.compose.material.icons.filled.Rule
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat
import com.example.smarthome.data.api.TokenManager
import com.example.smarthome.data.model.*
import com.example.smarthome.ui.components.*
import com.example.smarthome.ui.screens.*
import com.example.smarthome.ui.theme.SmartHomeTheme
import com.example.smarthome.ui.theme.PrimaryBlue
import com.example.smarthome.ui.theme.GrayText
import com.example.smarthome.ui.viewmodel.SmartHomeViewModel

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // Active le rendu bord à bord
        enableEdgeToEdge()
        
        // Configuration pour masquer les boutons de navigation (Mode Immersif)
        val windowInsetsController = WindowCompat.getInsetsController(window, window.decorView)
        windowInsetsController.systemBarsBehavior = WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
        windowInsetsController.hide(WindowInsetsCompat.Type.navigationBars())

        val tokenManager = TokenManager(this)
        setContent {
            SmartHomeTheme(dynamicColor = false) {
                val viewModel: SmartHomeViewModel = viewModel()

                // Initialisation de l'authentification au démarrage
                LaunchedEffect(Unit) {
                    viewModel.initAuth(tokenManager)
                }

                var showRegisterScreen by remember { mutableStateOf(false) }

                if (viewModel.isLoggedIn) {
                    SmartHomeApp(
                        viewModel = viewModel,
                        onCreateAccountClick = {
                            viewModel.logout()
                            showRegisterScreen = true
                        }
                    )
                } else if (showRegisterScreen) {
                    RegisterScreen(
                        viewModel = viewModel,
                        onBackToLogin = { showRegisterScreen = false }
                    )
                } else {
                    LoginScreen(
                        viewModel = viewModel,
                        onCreateAccountClick = { showRegisterScreen = true }
                    )
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
    onCreateAccountClick: () -> Unit = {}
) {
    var currentDestination by rememberSaveable { mutableStateOf(AppDestinations.HOME) }
    var selectedLampId by rememberSaveable { mutableStateOf<Int?>(null) }
    var showAIScreen by rememberSaveable { mutableStateOf(false) }
    var showRuleScreen by rememberSaveable { mutableStateOf(false) }
    var showAddDevice by rememberSaveable { mutableStateOf(false) }
    
    val devices by viewModel.devices
    val snackbarHostState = remember { SnackbarHostState() }

    if (showAIScreen) {
        AIScreen(
            viewModel = viewModel,
            onBack = { showAIScreen = false }
        )
    }
    else {
        Scaffold(
            modifier = Modifier.fillMaxSize(),
            containerColor = MaterialTheme.colorScheme.background,
            snackbarHost = { SnackbarHost(snackbarHostState) },

            bottomBar = {
                NavigationBar(
                    modifier = Modifier
                        .padding(start = 16.dp, end = 16.dp, bottom = 30.dp) // Encore plus haut
                        .shadow(
                            elevation = 8.dp, 
                            shape = RoundedCornerShape(24.dp),
                            clip = false
                        )
                        .height(64.dp) 
                        .clip(RoundedCornerShape(24.dp)),
                    containerColor = MaterialTheme.colorScheme.tertiary,
                    tonalElevation = 0.dp,
                    windowInsets = WindowInsets(0.dp) 
                ) {
                    AppDestinations.entries.forEach { dest ->
                        val isSelected = dest == currentDestination
                        NavigationBarItem(
                            icon = {
                                AnimatedVisibility(
                                    visible = isSelected,
                                    enter = fadeIn() + scaleIn() + expandVertically(),
                                    exit = fadeOut() + scaleOut() + shrinkVertically()
                                ) {
                                    Icon(
                                        dest.icon,
                                        contentDescription = dest.label,
                                        tint = PrimaryBlue,
                                        modifier = Modifier.size(18.dp)
                                    )
                                }
                            },
                            label = {
                                Text(
                                    dest.label,
                                    color = if (isSelected) PrimaryBlue else GrayText,
                                    fontSize = 10.sp
                                )
                            },
                            selected = isSelected,
                            alwaysShowLabel = true, 
                            onClick = {
                                currentDestination = dest
                                selectedLampId = null
                            },
                            colors = NavigationBarItemDefaults.colors(
                                indicatorColor = Color.Transparent
                            )
                        )
                    }
                }
            }
        ) { innerPadding ->
            val layoutDirection = LocalLayoutDirection.current
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(
                        top = innerPadding.calculateTopPadding(),
                        start = innerPadding.calculateStartPadding(layoutDirection),
                        end = innerPadding.calculateEndPadding(layoutDirection)
                    )
            ) {
                when (currentDestination) {
                    AppDestinations.HOME -> HomeScreen(
                        viewModel = viewModel,
                        selectedLampId = selectedLampId,
                        onLampSelect = { selectedLampId = it },
                        showAddDevice = showAddDevice,
                        onShowAddDeviceChange = { showAddDevice = it }
                    )
                    AppDestinations.RULES -> RulesScreen (viewModel = viewModel)
                    AppDestinations.DIMMING -> SmartDimmingScreen(viewModel = viewModel)
                    AppDestinations.PROFILE -> ProfileScreen(
                        name = viewModel.currentUsername,
                        email = viewModel.currentEmail,
                        onLogoutClick = { viewModel.logout() },
                        onAIIntelligenceClick = { showAIScreen = true },
                        onRulesClick = { showRuleScreen = true }
                    )
                }
            }
        }
    }
}


enum class AppDestinations(val label: String, val icon: ImageVector) {
    HOME("Accueil", Icons.Default.Home),
    RULES("Règles", Icons.Default.Rule),
    DIMMING("Dimming", Icons.Default.AutoAwesome),
    PROFILE("Profil", Icons.Default.AccountBox),
}

@Composable
fun darkTextFieldColors() = OutlinedTextFieldDefaults.colors(
    focusedBorderColor = Color(0xFF2979FF),
    unfocusedBorderColor = Color(0xFF2A3245),
    focusedTextColor = MaterialTheme.colorScheme.primary,
    unfocusedTextColor = MaterialTheme.colorScheme.primary,
    focusedLabelColor = Color(0xFF9AA4B2),
    unfocusedLabelColor = Color(0xFF9AA4B2),
    cursorColor = Color(0xFF2979FF),
    focusedLeadingIconColor = Color(0xFF9AA4B2),
    unfocusedLeadingIconColor = Color(0xFF9AA4B2),
    focusedTrailingIconColor = Color(0xFF9AA4B2),
    unfocusedTrailingIconColor = Color(0xFF9AA4B2)
)
