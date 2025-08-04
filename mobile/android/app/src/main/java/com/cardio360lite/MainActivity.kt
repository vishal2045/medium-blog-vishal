package com.cardio360lite

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.cardio360lite.ui.screens.HomeScreen
import com.cardio360lite.ui.screens.MonitoringScreen
import com.cardio360lite.ui.screens.AlertScreen
import com.cardio360lite.ui.screens.SettingsScreen
import com.cardio360lite.ui.theme.Cardio360LiteTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            Cardio360LiteTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    Cardio360LiteApp()
                }
            }
        }
    }
}

@Composable
fun Cardio360LiteApp() {
    val navController = rememberNavController()
    
    Scaffold(
        modifier = Modifier.fillMaxSize()
    ) { innerPadding ->
        NavHost(
            navController = navController,
            startDestination = "home",
            modifier = Modifier.padding(innerPadding)
        ) {
            composable("home") {
                HomeScreen(
                    onNavigateToMonitoring = {
                        navController.navigate("monitoring")
                    },
                    onNavigateToSettings = {
                        navController.navigate("settings")
                    }
                )
            }
            
            composable("monitoring") {
                MonitoringScreen(
                    onNavigateBack = {
                        navController.popBackStack()
                    },
                    onHighRiskDetected = {
                        navController.navigate("alert")
                    }
                )
            }
            
            composable("alert") {
                AlertScreen(
                    onNavigateBack = {
                        navController.popBackStack("home", inclusive = false)
                    }
                )
            }
            
            composable("settings") {
                SettingsScreen(
                    onNavigateBack = {
                        navController.popBackStack()
                    }
                )
            }
        }
    }
}

@Preview(showBackground = true)
@Composable
fun Cardio360LiteAppPreview() {
    Cardio360LiteTheme {
        Cardio360LiteApp()
    }
}