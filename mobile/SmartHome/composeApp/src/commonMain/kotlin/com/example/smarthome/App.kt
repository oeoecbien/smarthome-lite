package com.example.smarthome

import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AutoAwesome
import androidx.compose.material.icons.filled.Dashboard
import androidx.compose.material.icons.filled.ListAlt
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import com.smarthome.ui.screens.DashboardScreen
import com.smarthome.ui.screens.RulesScreen
import com.smarthome.ui.screens.SmartDimmingScreen
import org.jetbrains.compose.ui.tooling.preview.Preview

private sealed class Screen(val route: String, val title: String, val icon: ImageVector) {
    object Dashboard : Screen("dashboard", "Tableau de bord", Icons.Filled.Dashboard)
    object Rules : Screen("rules", "Règles", Icons.Filled.ListAlt)
    object SmartDimming : Screen("smart_dimming", "Smart Dimming", Icons.Filled.AutoAwesome)
}

private val screens = listOf(Screen.Dashboard, Screen.Rules, Screen.SmartDimming)

@Composable
@Preview
fun App() {
    MaterialTheme {
        var currentScreen by remember { mutableStateOf<Screen>(Screen.Dashboard) }

        Scaffold(
            bottomBar = {
                NavigationBar {
                    screens.forEach { screen ->
                        NavigationBarItem(
                            icon = { Icon(screen.icon, contentDescription = screen.title) },
                            label = { Text(screen.title) },
                            selected = currentScreen == screen,
                            onClick = { currentScreen = screen }
                        )
                    }
                }
            }
        ) { innerPadding ->
            when (currentScreen) {
                Screen.Dashboard -> DashboardScreen(Modifier.padding(innerPadding))
                Screen.Rules -> RulesScreen(Modifier.padding(innerPadding))
                Screen.SmartDimming -> SmartDimmingScreen(Modifier.padding(innerPadding))
            }
        }
    }
}