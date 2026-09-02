import 'package:flutter/material.dart';

class FriendTheme {
  static ThemeData build() {
    const canvas = Color(0xFF0B1020);
    const surface = Color(0xFF11192B);
    const surface2 = Color(0xFF182238);
    const primary = Color(0xFF6C8CFF);
    const success = Color(0xFF3DDC97);
    const warning = Color(0xFFF7C65C);
    const danger = Color(0xFFFF6B7A);
    const text = Color(0xFFF4F7FB);
    const muted = Color(0xFF9AA7BD);

    final scheme = ColorScheme.dark(
      surface: surface,
      surfaceContainerHighest: surface2,
      primary: primary,
      secondary: const Color(0xFF9B8CFF),
      error: danger,
      onSurface: text,
      onPrimary: Colors.white,
    );

    return ThemeData(
      useMaterial3: true,
      scaffoldBackgroundColor: canvas,
      colorScheme: scheme,
      dividerColor: const Color(0xFF2A3550),
      textTheme: const TextTheme(
        displaySmall: TextStyle(fontSize: 32, height: 1.2, fontWeight: FontWeight.w600, color: text),
        headlineSmall: TextStyle(fontSize: 22, height: 1.25, fontWeight: FontWeight.w600, color: text),
        titleLarge: TextStyle(fontSize: 20, height: 1.3, fontWeight: FontWeight.w600, color: text),
        titleMedium: TextStyle(fontSize: 16, height: 1.35, fontWeight: FontWeight.w600, color: text),
        bodyMedium: TextStyle(fontSize: 14, height: 1.45, color: text),
        bodySmall: TextStyle(fontSize: 12, height: 1.4, color: muted),
      ),
      cardTheme: const CardThemeData(
        color: surface,
        elevation: 0,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.all(Radius.circular(14))),
      ),
      inputDecorationTheme: const InputDecorationTheme(
        filled: true,
        fillColor: surface2,
        contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        border: OutlineInputBorder(borderRadius: BorderRadius.all(Radius.circular(10)), borderSide: BorderSide.none),
        enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.all(Radius.circular(10)), borderSide: BorderSide.none),
        focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.all(Radius.circular(10)), borderSide: BorderSide(color: primary, width: 1.2)),
      ),
      chipTheme: const ChipThemeData(
        backgroundColor: surface2,
        selectedColor: primary,
        side: BorderSide.none,
        padding: EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: primary,
          foregroundColor: Colors.white,
          minimumSize: const Size(0, 38),
          padding: const EdgeInsets.symmetric(horizontal: 14),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(9)),
        ),
      ),
      extensions: const <ThemeExtension<dynamic>>[
        FriendSemanticColors(success: success, warning: warning, danger: danger, muted: muted),
      ],
    );
  }
}

@immutable
class FriendSemanticColors extends ThemeExtension<FriendSemanticColors> {
  const FriendSemanticColors({required this.success, required this.warning, required this.danger, required this.muted});
  final Color success;
  final Color warning;
  final Color danger;
  final Color muted;

  @override
  FriendSemanticColors copyWith({Color? success, Color? warning, Color? danger, Color? muted}) => FriendSemanticColors(
        success: success ?? this.success,
        warning: warning ?? this.warning,
        danger: danger ?? this.danger,
        muted: muted ?? this.muted,
      );

  @override
  FriendSemanticColors lerp(covariant FriendSemanticColors? other, double t) {
    if (other == null) return this;
    return FriendSemanticColors(
      success: Color.lerp(success, other.success, t) ?? success,
      warning: Color.lerp(warning, other.warning, t) ?? warning,
      danger: Color.lerp(danger, other.danger, t) ?? danger,
      muted: Color.lerp(muted, other.muted, t) ?? muted,
    );
  }
}
