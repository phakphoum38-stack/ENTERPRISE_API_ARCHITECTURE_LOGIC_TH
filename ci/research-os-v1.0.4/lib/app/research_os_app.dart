import 'package:flutter/material.dart';

import '../screens/shell_page.dart';
import 'app_theme.dart';

class ResearchOsApp extends StatelessWidget {
  const ResearchOsApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Research OS',
      theme: AppTheme.dark(),
      home: const ShellPage(),
    );
  }
}
