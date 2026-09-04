import 'package:flutter/material.dart';

class FriendTheme {
  static ThemeData build() {
    const background = Color(0xFF080C16);
    const surface = Color(0xFF101725);
    const surfaceLow = Color(0xFF0D1420);
    const accent = Color(0xFF7DD3FC);
    const violet = Color(0xFFA78BFA);
    final scheme = ColorScheme.dark(
      surface: surface,
      surfaceContainer: surface,
      surfaceContainerLow: surfaceLow,
      surfaceContainerHighest: const Color(0xFF1A2434),
      primary: accent,
      secondary: violet,
      onSurface: const Color(0xFFE7EDF7),
      onSurfaceVariant: const Color(0xFF9AA8BB),
      outline: const Color(0xFF506176),
    );
    return ThemeData(
      useMaterial3: true,
      scaffoldBackgroundColor: background,
      colorScheme: scheme,
      visualDensity: VisualDensity.standard,
      cardTheme: CardThemeData(
        color: surface,
        elevation: 0,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16), side: BorderSide(color: scheme.outline.withValues(alpha: .10))),
      ),
      dividerTheme: DividerThemeData(color: scheme.outline.withValues(alpha: .10), space: 1),
      chipTheme: ChipThemeData(
        backgroundColor: surfaceLow,
        selectedColor: accent.withValues(alpha: .13),
        side: BorderSide(color: scheme.outline.withValues(alpha: .12)),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        labelStyle: const TextStyle(fontSize: 12),
      ),
      textTheme: const TextTheme(
        headlineSmall: TextStyle(fontWeight: FontWeight.w700, letterSpacing: -.3),
        titleLarge: TextStyle(fontWeight: FontWeight.w700, letterSpacing: -.2),
        titleMedium: TextStyle(fontWeight: FontWeight.w600),
        bodyLarge: TextStyle(height: 1.55),
        bodyMedium: TextStyle(height: 1.45),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: surfaceLow,
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: BorderSide(color: scheme.outline.withValues(alpha: .10))),
        enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: BorderSide(color: scheme.outline.withValues(alpha: .10))),
        focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: BorderSide(color: accent.withValues(alpha: .55), width: 1.2)),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(minimumSize: const Size(0, 46), padding: const EdgeInsets.symmetric(horizontal: 18), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(13))),
      ),
    );
  }
}
