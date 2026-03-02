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
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Favorite
import androidx.compose.material.icons.filled.Home
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
import com.example.smarthome.ui.viewmodel.SmartHomeViewModel

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
                                Icon(Icons.Filled.ArrowBack, contentDescription = "Back", tint = MaterialTheme.colorScheme.primary)
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