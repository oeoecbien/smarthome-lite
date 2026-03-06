package com.example.smarthome.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Add
import androidx.compose.material3.*
import androidx.compose.material3.pulltorefresh.PullToRefreshBox
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.smarthome.data.model.*
import com.example.smarthome.darkTextFieldColors
import com.example.smarthome.ui.theme.PrimaryBlue
import com.example.smarthome.ui.viewmodel.SmartHomeViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun RulesScreen(viewModel: SmartHomeViewModel) {
    val rules by viewModel.rules
    val isLoading by viewModel.isRulesLoading
    var showAddRule by remember { mutableStateOf(false) }

    if (showAddRule) {
        AddRuleScreen(
            viewModel = viewModel,
            onBack = { showAddRule = false }
        )
    } else {
        Scaffold(
            topBar = {
                TopAppBar(
                    title = { Text("Règles de gestion", color = MaterialTheme.colorScheme.primary) },
                    colors = TopAppBarDefaults.topAppBarColors(containerColor = Color.Transparent),
                )
            },
            floatingActionButton = {
                FloatingActionButton(
                    onClick = { showAddRule = true },
                    containerColor = PrimaryBlue,
                    contentColor = Color.White
                ) {
                    Icon(Icons.Default.Add, contentDescription = "Ajouter une règle")
                }
            },
            containerColor = MaterialTheme.colorScheme.background
        ) { innerPadding ->
            PullToRefreshBox(
                isRefreshing = isLoading,
                onRefresh = { viewModel.fetchRules() },
                modifier = Modifier
                    .fillMaxSize()
                    .padding(innerPadding)
            ) {
                if (rules.isEmpty() && !isLoading) {
                    Box(
                        modifier = Modifier
                            .fillMaxSize()
                            .verticalScroll(rememberScrollState()), // Permet le pull to refresh même si vide
                        contentAlignment = Alignment.Center
                    ) {
                        Text("Aucune règle configurée. Tirez pour rafraîchir.", color = Color.Gray)
                    }
                } else {
                    LazyColumn(
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(horizontal = 16.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp),
                        contentPadding = PaddingValues(bottom = 80.dp)
                    ) {
                        items(rules) { rule ->
                            RuleCard(
                                rule = rule,
                                onToggle = { enabled -> viewModel.toggleRule(rule.id, enabled) }
                            )
                        }
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AddRuleScreen(
    viewModel: SmartHomeViewModel,
    onBack: () -> Unit
) {
    var name by remember { mutableStateOf("") }
    var description by remember { mutableStateOf("") }
    var priority by remember { mutableStateOf("50") }
    
    // Condition Time
    var startTime by remember { mutableStateOf("08:00") }
    var endTime by remember { mutableStateOf("18:00") }
    
    // Action
    val devices by viewModel.devices
    var selectedDeviceId by remember { mutableStateOf<Int?>(null) }
    var brightness by remember { mutableStateOf("50") }
    
    var expandedDevices by remember { mutableStateOf(false) }

    val isAdding by viewModel.isLoading

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Nouvelle règle", color = MaterialTheme.colorScheme.primary) },
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
                .padding(24.dp)
                .verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            Text("Informations générales", color = Color.Gray, fontSize = 14.sp)

            OutlinedTextField(
                value = name,
                onValueChange = { name = it },
                label = { Text("Nom de la règle") },
                modifier = Modifier.fillMaxWidth(),
                colors = darkTextFieldColors(),
                shape = RoundedCornerShape(12.dp)
            )

            OutlinedTextField(
                value = description,
                onValueChange = { description = it },
                label = { Text("Description") },
                modifier = Modifier.fillMaxWidth(),
                colors = darkTextFieldColors(),
                shape = RoundedCornerShape(12.dp)
            )

            OutlinedTextField(
                value = priority,
                onValueChange = { if (it.all { c -> c.isDigit() }) priority = it },
                label = { Text("Priorité") },
                modifier = Modifier.fillMaxWidth(),
                colors = darkTextFieldColors(),
                shape = RoundedCornerShape(12.dp)
            )

            HorizontalDivider(modifier = Modifier.padding(vertical = 8.dp), color = Color(0xFF2A3245))
            
            Text("Conditions (Plage horaire & Présence)", color = Color.Gray, fontSize = 14.sp)
            
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(
                    value = startTime,
                    onValueChange = { startTime = it },
                    label = { Text("Début (HH:mm)") },
                    modifier = Modifier.weight(1f),
                    colors = darkTextFieldColors(),
                    shape = RoundedCornerShape(12.dp)
                )
                OutlinedTextField(
                    value = endTime,
                    onValueChange = { endTime = it },
                    label = { Text("Fin (HH:mm)") },
                    modifier = Modifier.weight(1f),
                    colors = darkTextFieldColors(),
                    shape = RoundedCornerShape(12.dp)
                )
            }

            HorizontalDivider(modifier = Modifier.padding(vertical = 8.dp), color = Color(0xFF2A3245))

            Text("Action", color = Color.Gray, fontSize = 14.sp)

            ExposedDropdownMenuBox(
                expanded = expandedDevices,
                onExpandedChange = { expandedDevices = it },
                modifier = Modifier.fillMaxWidth()
            ) {
                val selectedDeviceName = devices.find { it.id == selectedDeviceId }?.name ?: "Sélectionner un appareil"
                OutlinedTextField(
                    value = selectedDeviceName,
                    onValueChange = {},
                    readOnly = true,
                    label = { Text("Appareil") },
                    trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = expandedDevices) },
                    modifier = Modifier.menuAnchor().fillMaxWidth(),
                    colors = darkTextFieldColors(),
                    shape = RoundedCornerShape(12.dp)
                )
                ExposedDropdownMenu(
                    expanded = expandedDevices,
                    onDismissRequest = { expandedDevices = false },
                    modifier = Modifier.background(MaterialTheme.colorScheme.tertiary)
                ) {
                    devices.filterIsInstance<SmartLight>().forEach { device ->
                        DropdownMenuItem(
                            text = { Text(device.name, color = MaterialTheme.colorScheme.primary) },
                            onClick = {
                                selectedDeviceId = device.id
                                expandedDevices = false
                            }
                        )
                    }
                }
            }

            OutlinedTextField(
                value = brightness,
                onValueChange = { if (it.all { c -> c.isDigit() }) brightness = it },
                label = { Text("Luminosité (%)") },
                modifier = Modifier.fillMaxWidth(),
                colors = darkTextFieldColors(),
                shape = RoundedCornerShape(12.dp)
            )

            Spacer(modifier = Modifier.height(24.dp))

            Button(
                onClick = {
                    val ruleReq = RuleRequest(
                        name = name,
                        description = description,
                        enabled = true,
                        priority = priority.toIntOrNull() ?: 50,
                        condition = RuleCondition(
                            type = "AND",
                            conditions = listOf(
                                ConditionItem(type = "time", value = listOf(startTime, endTime), operator = "between"),
                                ConditionItem(type = "presence", value = true)
                            )
                        ),
                        action = RuleAction(
                            action = "set_brightness",
                            deviceId = selectedDeviceId ?: 0,
                            brightness = brightness.toIntOrNull() ?: 50
                        )
                    )
                    viewModel.createRule(ruleReq) {
                        onBack()
                    }
                },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(56.dp),
                shape = RoundedCornerShape(12.dp),
                colors = ButtonDefaults.buttonColors(containerColor = PrimaryBlue),
                enabled = name.isNotBlank() && selectedDeviceId != null && !isAdding
            ) {
                if (isAdding) {
                    CircularProgressIndicator(color = Color.White, modifier = Modifier.size(24.dp))
                } else {
                    Text("CRÉER LA RÈGLE", fontWeight = FontWeight.Bold)
                }
            }
        }
    }
}

@Composable
fun RuleCard(
    rule: RuleResponse,
    onToggle: (Boolean) -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.tertiary)
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = rule.name,
                    color = MaterialTheme.colorScheme.primary,
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Bold
                )
                Switch(
                    checked = rule.enabled,
                    onCheckedChange = { onToggle(it) },
                    colors = SwitchDefaults.colors(
                        checkedThumbColor = Color.White,
                        checkedTrackColor = PrimaryBlue
                    )
                )
            }
            Text(text = rule.description, color = MaterialTheme.colorScheme.primary, fontSize = 14.sp)
        }
    }
}
