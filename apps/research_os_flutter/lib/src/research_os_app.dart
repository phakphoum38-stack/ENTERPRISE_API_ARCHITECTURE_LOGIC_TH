import 'package:flutter/material.dart';

import 'api/research_os_api_client.dart';
import 'features/home/home_page.dart';

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
      home: HomePage(
        apiClient: ResearchOSApiClient(baseUrl: apiBaseUrl),
      ),
    );
  }
}
