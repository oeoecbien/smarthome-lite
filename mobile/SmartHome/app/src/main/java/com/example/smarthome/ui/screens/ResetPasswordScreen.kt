package com.example.smarthome.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.Visibility
import androidx.compose.material.icons.filled.VisibilityOff
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.smarthome.darkTextFieldColors
import com.example.smarthome.ui.viewmodel.SmartHomeViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ResetPasswordScreen(
    viewModel: SmartHomeViewModel,
    onBackToLogin: () -> Unit
) {
    var step by remember { mutableIntStateOf(1) }
    var usernameOrEmail by remember { mutableStateOf("") }
    var tokenState by remember { mutableStateOf("") }
    var newPassword by remember { mutableStateOf("") }
    var confirmPassword by remember { mutableStateOf("") }
    var passwordVisible by remember { mutableStateOf(false) }

    val isLoading by viewModel.isLoading
    val error by viewModel.errorMessage
    val forgotSuccess by viewModel.forgotPasswordSuccess
    val resetSuccess by viewModel.resetPasswordSuccess
    val isDarkTheme = isSystemInDarkTheme()

    // Fonction pour extraire le token du message
    fun extractToken(message: String?): String? {
        if (message == null) return null
        val regex = Regex("""token\s*(?:est)?\s*:\s*([^\s\(\)]+)""", RegexOption.IGNORE_CASE)
        return regex.find(message)?.groupValues?.get(1)
    }

    // Extraction automatique dès que le message de succès arrive
    LaunchedEffect(forgotSuccess) {
        extractToken(forgotSuccess)?.let {
            tokenState = it
        }
    }

    val backgroundModifier = if (isDarkTheme) {
        Modifier.background(
            Brush.verticalGradient(
                colors = listOf(Color(0xFF0A1A33), Color(0xFF060B16))
            )
        )
    } else {
        Modifier.background(MaterialTheme.colorScheme.background)
    }

    val titleColor = if (isDarkTheme) Color.White else MaterialTheme.colorScheme.onBackground

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Réinitialisation", color = titleColor) },
                navigationIcon = {
                    IconButton(onClick = onBackToLogin) {
                        Icon(
                            Icons.AutoMirrored.Filled.ArrowBack,
                            contentDescription = "Retour",
                            tint = titleColor
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = Color.Transparent)
            )
        },
        modifier = Modifier.fillMaxSize()
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .then(backgroundModifier)
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 24.dp)
                    .align(Alignment.Center),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                if (step == 1) {
                    Text(
                        text = "Étape 1 : Demander un token",
                        color = titleColor,
                        fontSize = 20.sp,
                        fontWeight = FontWeight.Bold
                    )
                    Spacer(modifier = Modifier.height(16.dp))
                    Text(
                        text = "Entrez votre nom d'utilisateur ou email pour recevoir votre code de réinitialisation.",
                        color = if (isDarkTheme) Color.LightGray else Color.Gray,
                        modifier = Modifier.padding(bottom = 24.dp)
                    )

                    OutlinedTextField(
                        value = usernameOrEmail,
                        onValueChange = { usernameOrEmail = it },
                        label = { Text("Utilisateur ou Email") },
                        singleLine = true,
                        leadingIcon = { Icon(Icons.Default.Person, contentDescription = null) },
                        modifier = Modifier.fillMaxWidth(),
                        colors = if (isDarkTheme) darkTextFieldColors() else OutlinedTextFieldDefaults.colors()
                    )

                    Spacer(modifier = Modifier.height(24.dp))

                    if (error != null) {
                        Text(error!!, color = MaterialTheme.colorScheme.error)
                        Spacer(modifier = Modifier.height(16.dp))
                    }

                    if (forgotSuccess != null) {
                        Text(forgotSuccess!!, color = Color.Green)
                        Spacer(modifier = Modifier.height(16.dp))
                        Button(
                            onClick = { 
                                // On s'assure que le token est bien extrait avant de passer à l'étape 2
                                extractToken(forgotSuccess)?.let { tokenState = it }
                                step = 2 
                            },
                            modifier = Modifier.fillMaxWidth(),
                            shape = RoundedCornerShape(14.dp)
                        ) {
                            Text("Passer à l'étape suivante")
                        }
                    } else {
                        Button(
                            onClick = { viewModel.forgotPassword(usernameOrEmail) },
                            enabled = !isLoading && usernameOrEmail.isNotBlank(),
                            modifier = Modifier.fillMaxWidth().height(52.dp),
                            shape = RoundedCornerShape(14.dp),
                            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF2979FF))
                        ) {
                            if (isLoading) {
                                CircularProgressIndicator(modifier = Modifier.size(24.dp), color = Color.White)
                            } else {
                                Text("Envoyer le code", color = Color.White)
                            }
                        }
                    }
                } else {
                    Text(
                        text = "Étape 2 : Nouveau mot de passe",
                        color = titleColor,
                        fontSize = 20.sp,
                        fontWeight = FontWeight.Bold
                    )
                    Spacer(modifier = Modifier.height(24.dp))

                    OutlinedTextField(
                        value = tokenState,
                        onValueChange = { tokenState = it },
                        label = { Text("Code de réinitialisation (Token)") },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth(),
                        colors = if (isDarkTheme) darkTextFieldColors() else OutlinedTextFieldDefaults.colors()
                    )

                    Spacer(modifier = Modifier.height(16.dp))

                    OutlinedTextField(
                        value = newPassword,
                        onValueChange = { newPassword = it },
                        label = { Text("Nouveau mot de passe") },
                        leadingIcon = { Icon(Icons.Default.Lock, contentDescription = null) },
                        trailingIcon = {
                            IconButton(onClick = { passwordVisible = !passwordVisible }) {
                                Icon(
                                    if (passwordVisible) Icons.Filled.Visibility else Icons.Filled.VisibilityOff,
                                    contentDescription = null
                                )
                            }
                        },
                        visualTransformation = if (passwordVisible) VisualTransformation.None else PasswordVisualTransformation(),
                        modifier = Modifier.fillMaxWidth(),
                        colors = if (isDarkTheme) darkTextFieldColors() else OutlinedTextFieldDefaults.colors()
                    )

                    Spacer(modifier = Modifier.height(16.dp))

                    OutlinedTextField(
                        value = confirmPassword,
                        onValueChange = { confirmPassword = it },
                        label = { Text("Confirmer le mot de passe") },
                        leadingIcon = { Icon(Icons.Default.Lock, contentDescription = null) },
                        visualTransformation = if (passwordVisible) VisualTransformation.None else PasswordVisualTransformation(),
                        modifier = Modifier.fillMaxWidth(),
                        colors = if (isDarkTheme) darkTextFieldColors() else OutlinedTextFieldDefaults.colors()
                    )

                    Spacer(modifier = Modifier.height(24.dp))

                    if (error != null) {
                        Text(error!!, color = MaterialTheme.colorScheme.error)
                        Spacer(modifier = Modifier.height(16.dp))
                    }

                    if (resetSuccess != null) {
                        Text(resetSuccess!!, color = Color.Green)
                    } else {
                        Button(
                            onClick = { 
                                if (newPassword == confirmPassword) {
                                    viewModel.resetPassword(newPassword, tokenState, onBackToLogin)
                                }
                            },
                            enabled = !isLoading && tokenState.isNotBlank() && newPassword.isNotBlank() && newPassword == confirmPassword,
                            modifier = Modifier.fillMaxWidth().height(52.dp),
                            shape = RoundedCornerShape(14.dp),
                            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF2979FF))
                        ) {
                            if (isLoading) {
                                CircularProgressIndicator(modifier = Modifier.size(24.dp), color = Color.White)
                            } else {
                                Text("Changer le mot de passe", color = Color.White)
                            }
                        }
                    }
                }
            }
        }
    }
}
