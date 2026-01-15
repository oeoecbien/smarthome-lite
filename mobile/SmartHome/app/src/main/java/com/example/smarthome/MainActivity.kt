package com.example.smarthome

import androidx.compose.animation.Crossfade
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.AccountBox
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Favorite
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
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
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.tooling.preview.PreviewScreenSizes
import androidx.compose.ui.unit.dp
import com.example.smarthome.ui.theme.SmartHomeTheme
import androidx.lifecycle.viewmodel.compose.viewModel

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            SmartHomeTheme {
                SmartHomeApp()
            }
        }
    }
}



@Preview(
    showBackground = true,
    showSystemUi = true
)

// Fonction qui permet d'avoir la View Home et de gérer l'affichage des autres avec les boutons navigation
@Composable
fun SmartHomeApp() {
    var currentDestination by rememberSaveable { mutableStateOf(AppDestinations.HOME) }

    NavigationSuiteScaffold(
        navigationSuiteItems = {
            AppDestinations.entries.forEach {
                item(
                    icon = {
                        Icon(
                            it.icon,
                            contentDescription = it.label
                        )
                    },
                    label = { Text(it.label) },
                    selected = it == currentDestination,
                    onClick = { currentDestination = it }
                )
            }
        }
    ) {
        Scaffold(modifier = Modifier.fillMaxSize()) { innerPadding ->
            Box(modifier = Modifier.padding(innerPadding)) {
                when (currentDestination) {
                    AppDestinations.HOME -> HomeScreen()
                    AppDestinations.FAVORITES -> FavoritesScreen()
                    AppDestinations.PROFILE -> GreetingName(name = "Profile")
                }
            }
        }
    }
}


enum class AppDestinations(
    val label: String,
    val icon: ImageVector,
) {
    HOME("Home", Icons.Default.Home),
    FAVORITES("Favorites", Icons.Default.Favorite),
    PROFILE("Profile", Icons.Default.AccountBox),
}


// Page Home
@Composable
fun HomeScreen(
    modifier: Modifier = Modifier,
    // On injecte le ViewModel ici
    viewModel: SmartHomeViewModel = viewModel()
) {
    // On observe les données du ViewModel
    val lamps by viewModel.lamps
    val error by viewModel.errorMessage

    var selectedLampId by remember { mutableStateOf<Int?>(null) }

    Crossfade(targetState = selectedLampId, label = "PageTransition") { lampId ->
        if (lampId == null) {
            Column(modifier = modifier.fillMaxSize().padding(16.dp)) {
                Text(
                    text = "Bonjour Melih,",
                    style = MaterialTheme.typography.headlineMedium,
                    fontWeight = FontWeight.Bold
                )

                // Affichage d'erreur si besoin
                if (error != null) {
                    Text(
                        text = error ?: "",
                        color = MaterialTheme.colorScheme.error,
                        modifier = Modifier.padding(vertical = 8.dp)
                    )
                    Button(onClick = { /* Relancer loadData() si tu l'exposes */ }) {
                        Text("Réessayer")
                    }
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
            modifier = Modifier.fillMaxSize().padding(16.dp),
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
                    imageVector = Icons.Default.Info, // Tu peux mettre Icons.Filled.Lightbulb si tu as la lib extended
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
    Column(modifier = Modifier.fillMaxSize()) {
        // Barre supérieure avec bouton retour
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            IconButton(onClick = onBack) {
                Icon(Icons.Default.ArrowBack, contentDescription = "Retour")
            }
            Spacer(modifier = Modifier.width(8.dp))
            Text(text = "Contrôle", style = MaterialTheme.typography.titleLarge)
        }

        // Contenu des contrôles
        Column(
            modifier = Modifier
                .padding(24.dp)
                .fillMaxWidth(),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            // Icône géante représentant la lampe
            Icon(
                imageVector = Icons.Default.Settings, // Remplace par Lightbulb si dispo
                contentDescription = null,
                modifier = Modifier.size(100.dp),
                tint = if (lamp.isOn) Color(0xFFFFC107) else Color.Gray // Jaune si allumé
            )

            Spacer(modifier = Modifier.height(24.dp))

            Text(
                text = lamp.name,
                style = MaterialTheme.typography.headlineMedium,
                fontWeight = FontWeight.Bold
            )

            Spacer(modifier = Modifier.height(48.dp))

            // Switch ON/OFF
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text("État", style = MaterialTheme.typography.titleMedium)
                Switch(
                    checked = lamp.isOn,
                    onCheckedChange = { isChecked ->
                        onUpdate(lamp.copy(isOn = isChecked))
                    }
                )
            }

            Spacer(modifier = Modifier.height(24.dp))

            // Slider Luminosité
            Text(
                text = "Luminosité ${(lamp.brightness * 100).toInt()}%",
                style = MaterialTheme.typography.titleMedium,
                modifier = Modifier.align(Alignment.Start)
            )
            Slider(
                value = lamp.brightness,
                onValueChange = { newBrightness ->
                    onUpdate(lamp.copy(brightness = newBrightness, isOn = true)) // Allume auto si on touche au slider
                },
                valueRange = 0f..1f
            )
        }
    }
}


// Reste des fonctions (Greeting, FavoritesScreen) inchangées...
@Composable
fun GreetingName(name: String, modifier: Modifier = Modifier) {
    Box(modifier = modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        Text(text = "Profil de $name!")
    }
}


@Composable
fun FavoritesScreen(modifier: Modifier = Modifier) {
    Box(modifier = modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        Text(text = "Tes favoris")
    }
}
