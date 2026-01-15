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
import androidx.compose.material.icons.filled.Settings
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


// --- Modèle de données simple pour une lampe ---
data class SmartLamp(
    val id: Int,
    val name: String,
    val isOn: Boolean,
    val brightness: Float // 0.0 à 1.0
)

@Preview
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
                    AppDestinations.PROFILE -> Greeting(name = "Profile")
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


@Composable
fun HomeScreen(modifier: Modifier = Modifier) {
    // Liste fictive de lampes
    var lamps by remember {
        mutableStateOf(
            listOf(
                SmartLamp(1, "Salon Principal", true, 0.8f),
                SmartLamp(2, "Lampe Bureau", false, 0.0f),
                SmartLamp(3, "Cuisine", true, 0.5f)
            )
        )
    }

    // État pour savoir quelle lampe est sélectionnée (null = aucune, on est sur l'accueil)
    var selectedLampId by remember { mutableStateOf<Int?>(null) }

    // Navigation interne à l'écran Home :
    // Si une lampe est sélectionnée, on affiche les détails, sinon la liste.
    Crossfade(targetState = selectedLampId, label = "PageTransition") { lampId ->
        if (lampId == null) {
            // --- VUE LISTE (ACCUEIL) ---
            Column(modifier = modifier.fillMaxSize().padding(16.dp)) {
                Text(
                    text = "Bonjour Melih,",
                    style = MaterialTheme.typography.headlineMedium,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    text = "Voici tes appareils connectés",
                    style = MaterialTheme.typography.bodyLarge,
                    color = Color.Gray,
                    modifier = Modifier.padding(bottom = 24.dp)
                )

                // Grille pour afficher les lampes
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
            // --- VUE DÉTAILS (PARAMÈTRES) ---
            // On récupère la lampe sélectionnée
            val activeLampIndex = lamps.indexOfFirst { it.id == lampId }
            if (activeLampIndex != -1) {
                LampControlScreen(
                    lamp = lamps[activeLampIndex],
                    onBack = { selectedLampId = null }, // Retour à la liste
                    onUpdate = { updatedLamp ->
                        // Mise à jour de la liste avec les nouvelles valeurs
                        val newLamps = lamps.toMutableList()
                        newLamps[activeLampIndex] = updatedLamp
                        lamps = newLamps
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
                    imageVector = Icons.Default.Settings, // Tu peux mettre Icons.Filled.Lightbulb si tu as la lib extended
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
fun Greeting(name: String, modifier: Modifier = Modifier) {
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
