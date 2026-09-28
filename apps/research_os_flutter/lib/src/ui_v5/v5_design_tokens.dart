import 'package:flutter/material.dart';

import '../ui/research_os_design_tokens.dart';

/// Shared visual language for the V5 Friend-centric UI.
///
/// Tokens intentionally derive from the active Material color scheme so V5 can
/// support light/dark themes without introducing a second hard-coded palette.
abstract final class ResearchOSV5Tokens {
  static const double pagePadding = ResearchOSDesignTokens.pagePadding;
  static const double sectionGap = ResearchOSDesignTokens.sectionGap;
  static const double panelGap = ResearchOSDesignTokens.panelGap;
  static const double compactRadius = ResearchOSDesignTokens.compactRadius;
  static const double panelRadius = ResearchOSDesignTokens.panelRadius;
  static const double largeRadius = ResearchOSDesignTokens.largeRadius;
  static const double sidebarWidth = 248;
  static const double contextWidth = 300;
  static const double composerMaxWidth = 900;

  static const Duration fastMotion = ResearchOSDesignTokens.fastMotion;
  static const Duration standardMotion = ResearchOSDesignTokens.standardMotion;

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
