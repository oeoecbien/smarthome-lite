package com.example.smarthome.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Bolt
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Devices
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Schedule
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.smarthome.data.model.ConditionItem
import com.example.smarthome.data.model.RuleAction
import com.example.smarthome.data.model.RuleResponse
import com.example.smarthome.ui.theme.NeonBlue
import com.example.smarthome.ui.theme.PrimaryBlue
import com.example.smarthome.ui.viewmodel.SmartHomeViewModel
import java.text.SimpleDateFormat
import java.util.Locale
import java.util.TimeZone

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun RuleDetailsScreen(
    rule: RuleResponse,
    viewModel: SmartHomeViewModel,
    onBack: () -> Unit
) {
    val devices by viewModel.devices
    val rules by viewModel.rules
    val currentRule = rules.find { it.id == rule.id } ?: rule
    
    var showDeleteDialog by remember { mutableStateOf(false) }

    if (showDeleteDialog) {
        AlertDialog(
            onDismissRequest = { showDeleteDialog = false },
            title = { Text("Supprimer la règle", color = MaterialTheme.colorScheme.primary) },
            text = { Text("Êtes-vous sûr de vouloir supprimer cette règle ? Cette action est irréversible.", color = MaterialTheme.colorScheme.primary) },
            confirmButton = {
                TextButton(
                    onClick = {
                        viewModel.deleteRule(currentRule.id)
                        showDeleteDialog = false
                        onBack()
                    }
                ) {
                    Text("Supprimer", color = Color.Red)
                }
            },
            dismissButton = {
                TextButton(onClick = { showDeleteDialog = false }) {
                    Text("Annuler", color = Color.Gray)
                }
            },
            containerColor = MaterialTheme.colorScheme.tertiary,
        )
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Détails de la règle", color = MaterialTheme.colorScheme.primary) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(
                            Icons.AutoMirrored.Filled.ArrowBack,
                            contentDescription = "Retour",
                            tint = MaterialTheme.colorScheme.primary
                        )
                    }
                },
                actions = {
                    IconButton(onClick = { showDeleteDialog = true }) {
                        Icon(
                            Icons.Default.Delete,
                            contentDescription = "Supprimer",
                            tint = Color.Red
                        )
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
                .padding(horizontal = 20.dp)
                .verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(20.dp)
        ) {
            // Header Card with basic info
            InfoCard(
                rule = currentRule,
                onToggle = { enabled -> viewModel.toggleRule(currentRule.id, enabled) }
            )

            // Conditions Section
            SectionHeader(title = "Conditions de déclenchement", icon = Icons.Default.Schedule)
            currentRule.condition.conditions?.forEach { condition ->
                ConditionDetailCard(condition)
            }

            // Action Section
            SectionHeader(title = "Action à exécuter", icon = Icons.Default.Bolt)
            ActionDetailCard(
                action = currentRule.action, 
                deviceName = devices.find { it.id == currentRule.action.deviceId }?.name ?: "Appareil #${currentRule.action.deviceId}"
            )

            // Technical Info
            TechnicalInfoSection(currentRule)

            // Bouton de suppression en bas
            Button(
                onClick = { showDeleteDialog = true },
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 16.dp)
                    .height(56.dp),
                colors = ButtonDefaults.buttonColors(containerColor = Color.Red.copy(alpha = 0.1f)),
                shape = RoundedCornerShape(12.dp),
                border = androidx.compose.foundation.BorderStroke(1.dp, Color.Red.copy(alpha = 0.5f))
            ) {
                Icon(Icons.Default.Delete, contentDescription = null, tint = Color.Red)
                Spacer(modifier = Modifier.width(8.dp))
                Text("SUPPRIMER LA RÈGLE", color = Color.Red, fontWeight = FontWeight.Bold)
            }

            Spacer(modifier = Modifier.height(20.dp))
        }
    }
}

@Composable
fun InfoCard(rule: RuleResponse, onToggle: (Boolean) -> Unit) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(20.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.tertiary)
    ) {
        Column(
            modifier = Modifier.padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = rule.name,
                    style = MaterialTheme.typography.headlineSmall,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.primary,
                    modifier = Modifier.weight(1f)
                )
                Row(verticalAlignment = Alignment.CenterVertically) {
                    StatusBadge(enabled = rule.enabled)
                    Spacer(modifier = Modifier.width(8.dp))
                    Switch(
                        checked = rule.enabled,
                        onCheckedChange = onToggle,
                        colors = SwitchDefaults.colors(
                            checkedThumbColor = NeonBlue,
                            checkedTrackColor = NeonBlue.copy(alpha = 0.3f)
                        )
                    )
                }
            }
            
            Text(
                text = rule.description,
                style = MaterialTheme.typography.bodyLarge,
                color = MaterialTheme.colorScheme.primary.copy(alpha = 0.8f)
            )
            
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Default.Settings, contentDescription = null, tint = NeonBlue, modifier = Modifier.size(16.dp))
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = "Priorité : ${rule.priority}",
                    style = MaterialTheme.typography.bodyMedium,
                    color = Color.Gray
                )
            }
        }
    }
}

@Composable
fun StatusBadge(enabled: Boolean) {
    Surface(
        color = if (enabled) Color(0xFF2E7D32).copy(alpha = 0.2f) else Color(0xFFC62828).copy(alpha = 0.2f),
        shape = RoundedCornerShape(8.dp)
    ) {
        Text(
            text = if (enabled) "ACTIVÉE" else "DÉSACTIVÉE",
            color = if (enabled) Color(0xFF4CAF50) else Color(0xFFEF5350),
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
            style = MaterialTheme.typography.labelSmall,
            fontWeight = FontWeight.Bold
        )
    }
}

@Composable
fun SectionHeader(title: String, icon: ImageVector) {
    Row(
        modifier = Modifier.padding(top = 8.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Icon(icon, contentDescription = null, tint = PrimaryBlue, modifier = Modifier.size(24.dp))
        Spacer(modifier = Modifier.width(12.dp))
        Text(
            text = title,
            style = MaterialTheme.typography.titleMedium,
            color = MaterialTheme.colorScheme.primary,
            fontWeight = FontWeight.SemiBold
        )
    }
}

@Composable
fun ConditionDetailCard(condition: ConditionItem) {
    val (title, description) = when (condition.type) {
        "time" -> {
            val values = condition.value as? List<*>
            if (condition.operator == "between" && values?.size == 2) {
                "Plage horaire" to "Entre ${values[0]} et ${values[1]}"
            } else {
                "Heure" to "${condition.operator} ${condition.value}"
            }
        }
        "presence" -> {
            "Détection de présence" to if (condition.value == true) "Si une présence est détectée" else "Si aucune présence n'est détectée"
        }
        else -> condition.type.replaceFirstChar { if (it.isLowerCase()) it.titlecase(Locale.getDefault()) else it.toString() } to "${condition.operator ?: ""} ${condition.value}"
    }

    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.tertiary.copy(alpha = 0.5f))
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(40.dp)
                    .background(PrimaryBlue.copy(alpha = 0.1f), RoundedCornerShape(10.dp)),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = if (condition.type == "time") Icons.Default.Schedule else Icons.Default.Info,
                    contentDescription = null,
                    tint = PrimaryBlue,
                    modifier = Modifier.size(20.dp)
                )
            }
            Spacer(modifier = Modifier.width(16.dp))
            Column {
                Text(text = title, style = MaterialTheme.typography.labelMedium, color = Color.Gray)
                Text(text = description, style = MaterialTheme.typography.bodyLarge, color = MaterialTheme.colorScheme.primary)
            }
        }
    }
}

@Composable
fun ActionDetailCard(action: RuleAction, deviceName: String) {
    val actionText = when (action.action) {
        "set_brightness" -> "Régler la luminosité à ${action.brightness}%"
        "toggle_state" -> if (action.state == true) "Allumer l'appareil" else "Éteindre l'appareil"
        else -> action.action
    }

    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.tertiary.copy(alpha = 0.5f))
    ) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(
                    modifier = Modifier
                        .size(40.dp)
                        .background(NeonBlue.copy(alpha = 0.1f), RoundedCornerShape(10.dp)),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(Icons.Default.Devices, contentDescription = null, tint = NeonBlue, modifier = Modifier.size(20.dp))
                }
                Spacer(modifier = Modifier.width(16.dp))
                Column {
                    Text(text = "Appareil concerné", style = MaterialTheme.typography.labelMedium, color = Color.Gray)
                    Text(text = deviceName, style = MaterialTheme.typography.bodyLarge, color = MaterialTheme.colorScheme.primary)
                }
            }
            
            HorizontalDivider(color = Color.White.copy(alpha = 0.05f))
            
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(
                    modifier = Modifier
                        .size(40.dp)
                        .background(Color(0xFFFFB300).copy(alpha = 0.1f), RoundedCornerShape(10.dp)),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(Icons.Default.Bolt, contentDescription = null, tint = Color(0xFFFFB300), modifier = Modifier.size(20.dp))
                }
                Spacer(modifier = Modifier.width(16.dp))
                Column {
                    Text(text = "Action programmée", style = MaterialTheme.typography.labelMedium, color = Color.Gray)
                    Text(text = actionText, style = MaterialTheme.typography.bodyLarge, color = MaterialTheme.colorScheme.primary)
                }
            }
        }
    }
}

@Composable
fun TechnicalInfoSection(rule: RuleResponse) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(top = 16.dp),
        horizontalAlignment = Alignment.End,
        verticalArrangement = Arrangement.spacedBy(4.dp)
    ) {
        val inputFormat = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'", Locale.US).apply {
            timeZone = TimeZone.getTimeZone("UTC")
        }
        val outputFormat = SimpleDateFormat("dd MMMM yyyy 'à' HH:mm", Locale.FRENCH)
        
        val createdDate = try {
            val date = inputFormat.parse(rule.createdAt)
            if (date != null) outputFormat.format(date) else rule.createdAt
        } catch (e: Exception) {
            rule.createdAt
        }
        
        val updatedDate = try {
            val date = inputFormat.parse(rule.updatedAt)
            if (date != null) outputFormat.format(date) else rule.updatedAt
        } catch (e: Exception) {
            rule.updatedAt
        }

        Text(text = "Créée le $createdDate", style = MaterialTheme.typography.labelSmall, color = Color.Gray)
        Text(text = "Mise à jour le $updatedDate", style = MaterialTheme.typography.labelSmall, color = Color.Gray)
    }
}
