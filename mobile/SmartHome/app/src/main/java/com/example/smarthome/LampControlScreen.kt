package com.example.smarthome

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.gestures.detectVerticalDragGestures
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
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
import androidx.compose.material3.Slider
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.blur
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.RenderEffect
import androidx.compose.ui.graphics.Shader
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.graphics.TileMode
import androidx.compose.ui.graphics.graphicsLayer
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
    lamp: SmartLight,
    onBack: () -> Unit,
    onUpdate: (SmartLight) -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .padding(20.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {

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
            color = MaterialTheme.colorScheme.primary,
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
                        text = "État",
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.primary
                    )
                    Text(
                        text = if (isOn) "Allumer" else "Éteint",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.secondary
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
            }

            Row(
                verticalAlignment = Alignment.CenterVertically
            ) {
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

                Spacer(modifier = Modifier.width(8.dp))

                IconButton(onClick = { /* Todo: Settings */ }) {
                    Icon(
                        Icons.Default.Settings,
                        contentDescription = "Settings",
                        tint = MaterialTheme.colorScheme.primary
                    )
                }
            }

        }
    }
}



@Composable
fun VerticalNeonSlider(
    brightness: Float,
    isEnabled: Boolean,
    onBrightnessChange: (Float) -> Unit,
    modifier: Modifier = Modifier,
    neonColor: Color = Color(0xFF00F5FF)
) {
    val animatedBrightness by animateFloatAsState(
        targetValue = brightness.coerceIn(0f, 1f),
        label = "brightness_animation"
    )

    BoxWithConstraints(
        modifier = modifier
            .width(70.dp)
            .height(240.dp)
            .alpha(if (isEnabled) 1f else 0.35f),
        contentAlignment = Alignment.BottomCenter
    ) {

        val heightPx = constraints.maxHeight.toFloat()

        Box(
            modifier = Modifier
                .fillMaxSize()
                .clip(RoundedCornerShape(35.dp))
                .background(Color(0xFF050505))
                .pointerInput(isEnabled) {
                    if (!isEnabled) return@pointerInput

                    detectVerticalDragGestures { change, _ ->
                        val newValue = 1f - (change.position.y / heightPx)
                        onBrightnessChange(newValue.coerceIn(0f, 1f))
                    }
                }
        ) {

            // 🌫️ Halo flou large
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .fillMaxHeight(animatedBrightness)
                    .align(Alignment.BottomCenter)
                    .blur(40.dp)
                    .background(neonColor.copy(alpha = 0.9f))
            )

            // ✨ Glow intermédiaire
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .fillMaxHeight(animatedBrightness)
                    .align(Alignment.BottomCenter)
                    .background(
                        brush = Brush.verticalGradient(
                            colors = listOf(
                                neonColor.copy(alpha = 0.7f),
                                neonColor
                            )
                        ),
                        shape = RoundedCornerShape(35.dp)
                    )
            )

            // 💎 Centre lumineux
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .fillMaxHeight(animatedBrightness)
                    .align(Alignment.BottomCenter)
                    .background(
                        Color.White.copy(alpha = 0.15f),
                        shape = RoundedCornerShape(35.dp)
                    )
            )
        }
    }
}
