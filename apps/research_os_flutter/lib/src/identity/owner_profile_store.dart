import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'owner_profile.dart';

final ValueNotifier<OwnerProfile?> ownerProfileState =
    ValueNotifier<OwnerProfile?>(null);

class OwnerProfileStore {
  OwnerProfileStore._();

  static const _emailKey = 'research_os_owner_email_v1';
  static const _updatedAtKey = 'research_os_owner_updated_at_v1';

  static String normalizeEmail(String value) => value.trim().toLowerCase();

  static bool isValidEmail(String value) {
    final normalized = normalizeEmail(value);
    return RegExp(r'^[^\s@]+@[^\s@]+\.[^\s@]+$').hasMatch(normalized);
  }

  static Future<OwnerProfile?> load() async {
    final prefs = await SharedPreferences.getInstance();
    final email = normalizeEmail(prefs.getString(_emailKey) ?? '');
    if (email.isEmpty || !isValidEmail(email)) return null;

    final updatedAt = DateTime.tryParse(prefs.getString(_updatedAtKey) ?? '') ??
        DateTime.now().toUtc();
    return OwnerProfile(email: email, updatedAt: updatedAt);
  }

  static Future<void> loadIntoState() async {
    ownerProfileState.value = await load();
  }

  static Future<OwnerProfile> saveEmail(String value) async {
    final email = normalizeEmail(value);
    if (!isValidEmail(email)) {
      throw const FormatException('กรุณาใส่อีเมลที่ถูกต้อง');
    }

    final profile = OwnerProfile(
      email: email,
      updatedAt: DateTime.now().toUtc(),
    );
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_emailKey, profile.email);
    await prefs.setString(_updatedAtKey, profile.updatedAt.toIso8601String());
    ownerProfileState.value = profile;
    return profile;
  }

  static Future<void> signOut() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_emailKey);
    await prefs.remove(_updatedAtKey);
    ownerProfileState.value = null;
  }
}
