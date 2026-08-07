import 'package:flutter/material.dart';

import 'api/research_os_api_client.dart';
import 'app_shell.dart';

class ResearchOSApp extends StatelessWidget {
  const ResearchOSApp({super.key});

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
      themeMode: ThemeMode.system,
      home: ResearchOSAppShell(
        apiClient: ResearchOSApiClient(baseUrl: apiBaseUrl),
      ),
    );
  }
}
