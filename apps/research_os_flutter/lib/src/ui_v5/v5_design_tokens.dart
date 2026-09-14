import 'package:flutter/material.dart';

/// Shared visual language for the V5 Friend-centric UI.
///
/// Tokens intentionally derive from the active Material color scheme so V5 can
/// support light/dark themes without introducing a second hard-coded palette.
abstract final class ResearchOSV5Tokens {
  static const double pagePadding = 20;
  static const double sectionGap = 16;
  static const double panelGap = 12;
  static const double compactRadius = 14;
  static const double panelRadius = 20;
  static const double largeRadius = 28;
  static const double sidebarWidth = 248;
  static const double contextWidth = 300;
  static const double composerMaxWidth = 900;

  static const Duration fastMotion = Duration(milliseconds: 140);
  static const Duration standardMotion = Duration(milliseconds: 220);

  static ThemeData apply(ThemeData base) {
    final scheme = base.colorScheme;
    return base.copyWith(
      visualDensity: VisualDensity.standard,
      inputDecorationTheme: base.inputDecorationTheme.copyWith(
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(panelRadius),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(panelRadius),
          borderSide: BorderSide(color: scheme.outlineVariant),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(panelRadius),
          borderSide: BorderSide(color: scheme.primary, width: 1.5),
        ),
      ),
      cardTheme: base.cardTheme.copyWith(
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(panelRadius),
        ),
      ),
    );
  }
}
