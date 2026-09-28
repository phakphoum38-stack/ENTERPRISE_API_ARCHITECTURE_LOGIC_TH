import 'package:flutter/material.dart';

/// Platform UX tokens for the Research OS unified dark/light-beam visual language.
/// Values mirror current/RESEARCH_OS_UNIFIED_UX_LIGHT_BEAM_CONTRACT.json.
abstract final class ResearchOSDesignTokens {
  static const background = Color(0xFF080C16);
  static const surface = Color(0xFF101725);
  static const surfaceLow = Color(0xFF0D1420);
  static const surfaceHigh = Color(0xFF1A2434);

  static const textPrimary = Color(0xFFE7EDF7);
  static const textSecondary = Color(0xFF9AA8BB);
  static const outline = Color(0xFF506176);

  static const primary = Color(0xFF7DD3FC);
  static const secondary = Color(0xFFA78BFA);
  static const blue = Color(0xFF60A5FA);

  static const success = Color(0xFF34D399);
  static const warning = Color(0xFFFBBF24);
  static const error = Color(0xFFF87171);
  static const info = Color(0xFF60A5FA);

  static const pagePadding = 20.0;
  static const sectionGap = 16.0;
  static const panelGap = 12.0;
  static const compactRadius = 14.0;
  static const panelRadius = 20.0;
  static const largeRadius = 28.0;

  static const fastMotion = Duration(milliseconds: 140);
  static const standardMotion = Duration(milliseconds: 220);

  static BoxShadow beamGlow({
    Color color = primary,
    double opacity = .22,
    double blur = 28,
    double spread = -8,
  }) {
    return BoxShadow(
      color: color.withValues(alpha: opacity),
      blurRadius: blur,
      spreadRadius: spread,
    );
  }

  static LinearGradient upwardBeam({Color color = primary}) {
    return LinearGradient(
      begin: Alignment.bottomCenter,
      end: Alignment.topCenter,
      colors: [
        color.withValues(alpha: .30),
        color.withValues(alpha: .10),
        color.withValues(alpha: 0),
      ],
    );
  }

  static ThemeData darkTheme() {
    final scheme = ColorScheme.dark(
      surface: surface,
      surfaceContainer: surface,
      surfaceContainerLow: surfaceLow,
      surfaceContainerHighest: surfaceHigh,
      primary: primary,
      secondary: secondary,
      tertiary: blue,
      onSurface: textPrimary,
      onSurfaceVariant: textSecondary,
      outline: outline,
      error: error,
      onError: background,
    );

    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      colorScheme: scheme,
      scaffoldBackgroundColor: background,
      visualDensity: VisualDensity.standard,
      dividerTheme: DividerThemeData(
        color: outline.withValues(alpha: .18),
        space: 1,
      ),
      appBarTheme: const AppBarTheme(
        elevation: 0,
        scrolledUnderElevation: 0,
        backgroundColor: background,
        surfaceTintColor: Colors.transparent,
      ),
      cardTheme: CardThemeData(
        elevation: 0,
        margin: EdgeInsets.zero,
        color: surface,
        surfaceTintColor: Colors.transparent,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(panelRadius),
          side: BorderSide(color: outline.withValues(alpha: .18)),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: surfaceLow,
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(compactRadius),
          borderSide: BorderSide(color: outline.withValues(alpha: .18)),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(compactRadius),
          borderSide: BorderSide(color: outline.withValues(alpha: .18)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(compactRadius),
          borderSide: BorderSide(color: primary.withValues(alpha: .65), width: 1.2),
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: primary,
          foregroundColor: background,
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 13),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(compactRadius),
          ),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: textPrimary,
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 13),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(compactRadius),
          ),
          side: BorderSide(color: outline.withValues(alpha: .25)),
        ),
      ),
      chipTheme: ChipThemeData(
        backgroundColor: surfaceLow,
        selectedColor: primary.withValues(alpha: .13),
        side: BorderSide(color: outline.withValues(alpha: .18)),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(10),
        ),
        labelStyle: const TextStyle(fontSize: 12, color: textPrimary),
      ),
      listTileTheme: ListTileThemeData(
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 2),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(compactRadius),
        ),
      ),
    );
  }

  static ThemeData lightTheme() {
    final scheme = ColorScheme.fromSeed(
      seedColor: primary,
      brightness: Brightness.light,
      surface: const Color(0xFFF5F8FC),
    );
    return ThemeData(
      useMaterial3: true,
      colorScheme: scheme,
      scaffoldBackgroundColor: const Color(0xFFF5F8FC),
    );
  }
}
