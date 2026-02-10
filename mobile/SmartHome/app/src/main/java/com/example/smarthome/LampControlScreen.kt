package com.example.smarthome

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.gestures.detectVerticalDragGestures
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Lightbulb
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.outlined.WbSunny
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.smarthome.ui.theme.CardSurface
import com.example.smarthome.ui.theme.DarkSurface
import com.example.smarthome.ui.theme.NeonBlue
import com.example.smarthome.ui.theme.NeonBlueGlow
import com.example.smarthome.ui.theme.TextGreen

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