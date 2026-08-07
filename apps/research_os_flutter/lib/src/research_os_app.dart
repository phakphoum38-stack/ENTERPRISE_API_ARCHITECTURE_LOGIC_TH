import 'package:flutter/material.dart';

import 'api/research_os_api_client.dart';
import 'app_shell.dart';

class ResearchOSApp extends StatefulWidget {
  const ResearchOSApp({super.key});

  @override
  State<ResearchOSApp> createState() => _ResearchOSAppState();
}

class _ResearchOSAppState extends State<ResearchOSApp> {
  ThemeMode _themeMode = ThemeMode.system;

  @override
  Widget build(BuildContext context) {
    const apiBaseUrl = String.fromEnvironment(
      'RESEARCH_OS_API_BASE_URL',
      defaultValue: 'http://127.0.0.1:8787',
    );

    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Research OS',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.indigo),
        useMaterial3: true,
      ),
      darkTheme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.indigo,
          brightness: Brightness.dark,
        ),
        useMaterial3: true,
      ),
      themeMode: _themeMode,
      home: ResearchOSAppShell(
        apiClient: ResearchOSApiClient(baseUrl: apiBaseUrl),
        themeMode: _themeMode,
        onThemeModeChanged: (value) {
          setState(() => _themeMode = value);
        },
      ),
    );
  }
}
