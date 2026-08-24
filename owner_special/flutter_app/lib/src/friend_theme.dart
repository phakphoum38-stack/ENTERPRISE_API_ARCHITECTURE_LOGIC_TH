import 'package:flutter/material.dart';

class FriendTheme {
  static ThemeData build() {
    const background = Color(0xFF0B1020);
    const surface = Color(0xFF121A2B);
    const accent = Color(0xFF7DD3FC);
    return ThemeData(
      useMaterial3: true,
      scaffoldBackgroundColor: background,
      colorScheme: const ColorScheme.dark(
        surface: surface,
        primary: accent,
        secondary: Color(0xFFA78BFA),
      ),
      textTheme: const TextTheme(
        headlineSmall: TextStyle(fontWeight: FontWeight.w700),
        titleMedium: TextStyle(fontWeight: FontWeight.w600),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: surface,
        border: OutlineInputBorder(borderRadius: BorderRadius.all(Radius.circular(14)), borderSide: BorderSide.none),
      ),
    );
  }
}
