package com.example.smarthome

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AccountBox
import androidx.compose.material.icons.filled.Favorite
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.AutoAwesome
import androidx.compose.material.icons.filled.Notifications
import androidx.compose.material3.*
import androidx.compose.material3.adaptive.navigationsuite.NavigationSuiteDefaults
import androidx.compose.material3.adaptive.navigationsuite.NavigationSuiteScaffold
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.lifecycle.viewmodel.compose.viewModel
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
        enableEdgeToEdge()
        setContent {
            SmartHomeTheme(dynamicColor = false) {
                val viewModel: SmartHomeViewModel = viewModel()

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
    // Hoisted state for Lamp detail navigation
    var selectedLampId by rememberSaveable { mutableStateOf<Int?>(null) }
    // Observe lamps to get the name for the title
    val devices by viewModel.devices
    val snackbarHostState = remember { SnackbarHostState() }

    Scaffold(
        modifier = Modifier.fillMaxSize(),
        containerColor = MaterialTheme.colorScheme.background,
        snackbarHost = { SnackbarHost(snackbarHostState) },

        bottomBar = {
            NavigationBar(
                containerColor = MaterialTheme.colorScheme.tertiary
            ) {
                AppDestinations.entries.forEach { dest ->
                    NavigationBarItem(
                        icon = {
                            Icon(
                                dest.icon,
                                contentDescription = dest.label,
                                tint = if (dest == currentDestination) PrimaryBlue else GrayText
                            )
                        },
                        label = {
                            Text(
                                dest.label,
                                color = if (dest == currentDestination) PrimaryBlue else GrayText
                            )
                        },
                        selected = dest == currentDestination,
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
                AppDestinations.EVENTS -> EventsScreen(viewModel = viewModel)
                AppDestinations.DIMMING -> SmartDimmingScreen(viewModel = viewModel)
                AppDestinations.PROFILE -> ProfileScreen(
                    name = viewModel.currentUsername,
                    email = viewModel.currentEmail,
                    onLogoutClick = { viewModel.logout() },
                    onCreateAccountClick = onCreateAccountClick
                )
            }
        }
    }
}


enum class AppDestinations(val label: String, val icon: ImageVector) {
    HOME("Accueil", Icons.Default.Home),
    EVENTS("Événements", Icons.Default.Notifications),
    DIMMING("Dimming", Icons.Default.AutoAwesome),
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