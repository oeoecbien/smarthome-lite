package com.example.smarthome.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.smarthome.ui.theme.PrimaryBlue
import com.example.smarthome.ui.viewmodel.SmartHomeViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AIScreen(
    viewModel: SmartHomeViewModel,
    onBack: () -> Unit
) {
    val aiScenario by viewModel.aiScenario
    val isLoading by viewModel.isAILoading

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Intelligence Artificielle") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Retour")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.background,
                    titleContentColor = MaterialTheme.colorScheme.primary
                )
            )
        }
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(MaterialTheme.colorScheme.background)
                .padding(innerPadding)
        ) {
            if (isLoading && aiScenario == null) {
                CircularProgressIndicator(modifier = Modifier.align(Alignment.Center))
            } else if (aiScenario != null) {
                LazyColumn(
                    modifier = Modifier.fillMaxSize(),
                    contentPadding = PaddingValues(20.dp),
                    verticalArrangement = Arrangement.spacedBy(20.dp)
                ) {
                    // Scenario Card
                    item {
                        Card(
                            modifier = Modifier.fillMaxWidth(),
                            shape = RoundedCornerShape(24.dp),
                            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.tertiary)
                        ) {
                            Column(modifier = Modifier.padding(24.dp)) {
                                Text(
                                    "Scénario Actuel",
                                    style = MaterialTheme.typography.labelLarge,
                                    color = MaterialTheme.colorScheme.secondary
                                )
                                Spacer(modifier = Modifier.height(8.dp))
                                Text(
                                    aiScenario!!.scenarioName,
                                    style = MaterialTheme.typography.headlineLarge,
                                    fontWeight = FontWeight.Bold,
                                    color = MaterialTheme.colorScheme.primary
                                )
                                Spacer(modifier = Modifier.height(16.dp))
                                
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    val confidencePercent = (aiScenario!!.confidence * 100).toInt()
                                    LinearProgressIndicator(
                                        progress = aiScenario!!.confidence.toFloat(),
                                        modifier = Modifier.weight(1f).height(8.dp).clip(CircleShape),
                                        color = PrimaryBlue,
                                        trackColor = Color.Gray
                                    )
                                    Spacer(modifier = Modifier.width(16.dp))
                                    Text(
                                        "$confidencePercent%",
                                        fontWeight = FontWeight.Bold,
                                        color = MaterialTheme.colorScheme.primary
                                    )
                                }
                                Text(
                                    "Confiance de l'IA",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.secondary
                                )
                            }
                        }
                    }

                    // Context Grid
                    item {
                        Text(
                            "Contexte détecté",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.primary
                        )
                    }

                    item {
                        Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                                ContextItem(
                                    modifier = Modifier.weight(1f),
                                    icon = Icons.Default.Schedule,
                                    label = "Heure",
                                    value = "${aiScenario!!.context.hour}h"
                                )
                                ContextItem(
                                    modifier = Modifier.weight(1f),
                                    icon = Icons.Default.People,
                                    label = "Présence",
                                    value = if (aiScenario!!.context.presenceDetected) "Oui" else "Non"
                                )
                            }
                            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                                ContextItem(
                                    modifier = Modifier.weight(1f),
                                    icon = Icons.Default.Lightbulb,
                                    label = "Lumière",
                                    value = if (aiScenario!!.context.lightOn) "Allumée" else "Éteinte"
                                )
                                ContextItem(
                                    modifier = Modifier.weight(1f),
                                    icon = Icons.Default.Psychology,
                                    label = "Méthode",
                                    value = aiScenario!!.method.uppercase()
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun ContextItem(
    modifier: Modifier = Modifier,
    icon: ImageVector,
    label: String,
    value: String
) {
    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(16.dp),
        color = MaterialTheme.colorScheme.tertiary
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(
                icon,
                contentDescription = null,
                modifier = Modifier.size(24.dp),
                tint = MaterialTheme.colorScheme.primary
            )
            Spacer(modifier = Modifier.width(12.dp))
            Column {
                Text(label, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.secondary)
                Text(value, style = MaterialTheme.typography.bodyMedium, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.primary)
            }
        }
    }
}
