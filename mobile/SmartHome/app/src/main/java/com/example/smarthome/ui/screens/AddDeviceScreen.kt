package com.example.smarthome.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.smarthome.darkTextFieldColors
import com.example.smarthome.ui.theme.PrimaryBlue
import com.example.smarthome.ui.viewmodel.SmartHomeViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AddDeviceScreen(
    viewModel: SmartHomeViewModel,
    onBack: () -> Unit
) {
    var name by remember { mutableStateOf("") }
    var type by remember { mutableStateOf("dimmer") } // "dimmer" ou "sensor"
    var gpioPin by remember { mutableStateOf("") }
    var raspberryId by remember { mutableStateOf("1") }

    val isLoading by viewModel.isLoading
    val errorMessage by viewModel.errorMessage

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Ajouter un appareil", color = MaterialTheme.colorScheme.primary) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Retour", tint = MaterialTheme.colorScheme.primary)
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = Color.Transparent)
            )
        },
        containerColor = MaterialTheme.colorScheme.background
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .padding(24.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            OutlinedTextField(
                value = name,
                onValueChange = { name = it },
                label = { Text("Nom de l'appareil") },
                modifier = Modifier.fillMaxWidth(),
                colors = darkTextFieldColors(),
                shape = RoundedCornerShape(12.dp)
            )

            // Sélection du Type
            Column(modifier = Modifier.fillMaxWidth()) {
                Text("Type d'appareil", color = Color.Gray, fontSize = 14.sp)
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    val types = listOf("dimmer", "sensor")
                    types.forEach { t ->
                        FilterChip(
                            selected = type == t,
                            onClick = { type = t },
                            label = { Text(t.replaceFirstChar { it.uppercase() }) },
                            colors = FilterChipDefaults.filterChipColors(
                                selectedContainerColor = PrimaryBlue,
                                selectedLabelColor = Color.White,
                                containerColor = Color(0xFF2A3245),
                                labelColor = Color.Gray
                            )
                        )
                    }
                }
            }

            OutlinedTextField(
                value = gpioPin,
                onValueChange = { if (it.all { char -> char.isDigit() }) gpioPin = it },
                label = { Text("GPIO PIN") },
                modifier = Modifier.fillMaxWidth(),
                colors = darkTextFieldColors(),
                shape = RoundedCornerShape(12.dp)
            )

            OutlinedTextField(
                value = raspberryId,
                onValueChange = { if (it.all { char -> char.isDigit() }) raspberryId = it },
                label = { Text("Raspberry Pi ID") },
                modifier = Modifier.fillMaxWidth(),
                colors = darkTextFieldColors(),
                shape = RoundedCornerShape(12.dp)
            )

            if (errorMessage != null) {
                Text(errorMessage!!, color = Color.Red, fontSize = 14.sp)
            }

            Spacer(modifier = Modifier.weight(1f))

            Button(
                onClick = {
                    val pin = gpioPin.toIntOrNull() ?: 0
                    val rId = raspberryId.toIntOrNull() ?: 1
                    viewModel.addDevice(name, type, pin, rId) {
                        onBack()
                    }
                },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(56.dp),
                shape = RoundedCornerShape(12.dp),
                colors = ButtonDefaults.buttonColors(containerColor = PrimaryBlue),
                enabled = name.isNotBlank() && gpioPin.isNotBlank() && !isLoading
            ) {
                if (isLoading) {
                    CircularProgressIndicator(color = Color.White, modifier = Modifier.size(24.dp))
                } else {
                    Text("AJOUTER", fontSize = 16.sp, fontWeight = FontWeight.Bold)
                }
            }
        }
    }
}
