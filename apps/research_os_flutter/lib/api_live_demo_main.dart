import 'package:flutter/material.dart';

import 'src/api/research_os_api_client.dart';
import 'src/features/api_live/api_live_demo_page.dart';

void main() {
  const baseUrl = String.fromEnvironment(
    'RESEARCH_OS_API_URL',
    defaultValue: 'http://127.0.0.1:8787',
  );

  runApp(MaterialApp(
    debugShowCheckedModeBanner: false,
    title: 'Flutter API Platform Live Demo',
    theme: ThemeData(useMaterial3: true, colorSchemeSeed: Colors.blue),
    home: ApiLiveDemoPage(
      apiClient: ResearchOSApiClient(baseUrl: baseUrl),
    ),
  ));
}
