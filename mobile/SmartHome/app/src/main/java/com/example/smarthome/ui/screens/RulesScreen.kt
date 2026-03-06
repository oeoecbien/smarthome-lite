package com.example.smarthome.ui.screens

import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material3.*
import androidx.compose.material3.pulltorefresh.PullToRefreshBox
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.smarthome.data.model.*
import com.example.smarthome.darkTextFieldColors
import com.example.smarthome.ui.theme.PrimaryBlue
import com.example.smarthome.ui.theme.TextWhite
import com.example.smarthome.ui.viewmodel.SmartHomeViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun RulesScreen(viewModel: SmartHomeViewModel) {
    val rules by viewModel.rules
    val isLoading by viewModel.isRulesLoading
    var showAddRule by remember { mutableStateOf(false) }
    var selectedRule by remember { mutableStateOf<RuleResponse?>(null) }
    var ruleToDelete by remember { mutableStateOf<RuleResponse?>(null) }

    if (showAddRule) {
        AddRuleScreen(
            viewModel = viewModel,
            onBack = { showAddRule = false }
        )
    } else if (selectedRule != null) {
        RuleDetailsScreen(
            rule = selectedRule!!,
            viewModel = viewModel,
            onBack = { selectedRule = null }
        )
    } else {
        if (ruleToDelete != null) {
            AlertDialog(
                onDismissRequest = { ruleToDelete = null },
                title = { Text("Supprimer la règle", color = MaterialTheme.colorScheme.primary) },
                text = { Text("Voulez-vous vraiment supprimer la règle '${ruleToDelete?.name}' ?", color = MaterialTheme.colorScheme.primary) },
                confirmButton = {
                    TextButton(onClick = {
                        ruleToDelete?.let { viewModel.deleteRule(it.id) }
                        ruleToDelete = null
                    }) {
                        Text("Supprimer", color = Color.Red)
                    }
                },
                dismissButton = {
                    TextButton(onClick = { ruleToDelete = null }) {
                        Text("Annuler", color = Color.Gray)
                    }
                },
                containerColor = MaterialTheme.colorScheme.tertiary
            )
        }

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
                    contentColor = Color.White,
                    modifier = Modifier.padding(bottom = 90.dp)
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
                            .verticalScroll(rememberScrollState()),
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
                        contentPadding = PaddingValues(bottom = 120.dp)
                    ) {
                        items(
                            items = rules,
                            key = { it.id }
                        ) { rule ->
                            val dismissState = rememberSwipeToDismissBoxState(
                                confirmValueChange = {
                                    if (it == SwipeToDismissBoxValue.EndToStart) {
                                        ruleToDelete = rule
                                        false // Empêche le dismiss immédiat pour montrer la boîte de dialogue
                                    } else {
                                        false
                                    }
                                },
                                positionalThreshold = { totalDistance -> totalDistance * 0.5f } // Seuil à 50%
                            )

                            SwipeToDismissBox(
                                state = dismissState,
                                enableDismissFromStartToEnd = false,
                                backgroundContent = {
                                    val color by animateColorAsState(
                                        when (dismissState.targetValue) {
                                            SwipeToDismissBoxValue.EndToStart -> Color.Red.copy(alpha = 0.8f)
                                            else -> Color.Transparent
                                        }, label = "backgroundColor"
                                    )
                                    val scale by animateFloatAsState(
                                        if (dismissState.targetValue == SwipeToDismissBoxValue.Settled) 0.75f else 1f,
                                        label = "scale"
                                    )

                                    Box(
                                        Modifier
                                            .fillMaxSize()
                                            .background(color, RoundedCornerShape(16.dp))
                                            .padding(horizontal = 20.dp),
                                        contentAlignment = Alignment.CenterEnd
                                    ) {
                                        Icon(
                                            Icons.Default.Delete,
                                            contentDescription = "Supprimer",
                                            modifier = Modifier.scale(scale),
                                            tint = Color.White
                                        )
                                    }
                                }
                            ) {
                                RuleCard(
                                    rule = rule,
                                    onToggle = { enabled -> viewModel.toggleRule(rule.id, enabled) },
                                    onClick = { selectedRule = rule }
                                )
                            }
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
                val selectedDevice = devices.find { it.id == selectedDeviceId }
                val selectedDeviceName = selectedDevice?.name ?: "Sélectionner un appareil"
                OutlinedTextField(
                    value = selectedDeviceName,
                    onValueChange = {},
                    readOnly = true,
                    label = { Text("Appareil") },
                    trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = expandedDevices) },
                    modifier = Modifier.menuAnchor(MenuAnchorType.PrimaryNotEditable, true).fillMaxWidth(),
                    colors = darkTextFieldColors(),
                    shape = RoundedCornerShape(12.dp)
                )
                ExposedDropdownMenu(
                    expanded = expandedDevices,
                    onDismissRequest = { expandedDevices = false },
                    modifier = Modifier.background(MaterialTheme.colorScheme.tertiary)
                ) {
                    devices.forEach { device ->
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
                    CircularProgressIndicator(color = Color.White, modifier = Modifier.size(24.dp), strokeWidth = 2.dp)
                } else {
                    Text("CRÉER LA RÈGLE", fontWeight = FontWeight.Bold, color = Color.White)
                }

            }
            Spacer(modifier = Modifier.height(100.dp))
        }
    }
}

@Composable
fun RuleCard(
    rule: RuleResponse,
    onToggle: (Boolean) -> Unit,
    onClick: () -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable { onClick() },
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.tertiary)
    ) {
        Row(
            modifier = Modifier
                .padding(20.dp)
                .fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = rule.name,
                    fontWeight = FontWeight.Bold,
                    fontSize = 18.sp,
                    color = MaterialTheme.colorScheme.primary
                )
                Text(
                    text = rule.description,
                    color = Color.Gray,
                    fontSize = 14.sp,
                    maxLines = 1
                )
            }

            Switch(
                checked = rule.enabled,
                onCheckedChange = { onToggle(it) },
                colors = SwitchDefaults.colors(
                    checkedThumbColor = TextWhite,
                    checkedTrackColor = PrimaryBlue,
                    uncheckedThumbColor = MaterialTheme.colorScheme.primary,
                    uncheckedTrackColor = MaterialTheme.colorScheme.background
                )
            )
        }
    }
}
