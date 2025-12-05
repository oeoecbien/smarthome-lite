package com.smarthome.ui.screens

import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import com.smarthome.ui.components.RuleCard

private data class Rule(val name: String, val condition: String, val action: String)

private val fakeRules = listOf(
    Rule(
        name = "Présence en soirée",
        condition = "Présence détectée & Heure entre 18h-23h",
        action = "Allumer la lampe du salon à 70%"
    ),
    Rule(
        name = "Économie d'énergie",
        condition = "Aucune présence pendant 10 minutes",
        action = "Éteindre toutes les lampes"
    ),
    Rule(
        name = "Lumière du jour",
        condition = "Luminosité > 500 lux",
        action = "Réduire lampe bureau à 20%"
    )
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun RulesScreen(modifier: Modifier = Modifier) {
    Scaffold(
        modifier = modifier,
        topBar = { TopAppBar(title = { Text("Règles d'automatisation") }) }
    ) {
        LazyColumn(modifier = Modifier.padding(it)) {
            items(fakeRules) { rule ->
                RuleCard(
                    ruleName = rule.name,
                    condition = rule.condition,
                    action = rule.action
                )
            }
        }
    }
}
