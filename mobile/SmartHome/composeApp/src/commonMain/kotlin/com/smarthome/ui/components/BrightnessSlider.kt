package com.smarthome.ui.components

import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Lightbulb
import androidx.compose.material3.Icon
import androidx.compose.material3.Slider
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun BrightnessSlider(
    // We'll replace this with a real value later
) {
    var brightness by remember { mutableStateOf(50f) }

    Row(
        verticalAlignment = Alignment.CenterVertically,
        modifier = Modifier.padding(horizontal = 16.dp)
    ) {
        Icon(Icons.Filled.Lightbulb, contentDescription = "Brightness")
        Slider(
            value = brightness,
            onValueChange = { brightness = it },
            valueRange = 0f..100f,
            modifier = Modifier.weight(1f)
        )
    }
}
