import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

final ValueNotifier<String> selectedProviderState = ValueNotifier<String>('gemini');

class ProviderSelectionStore {
  ProviderSelectionStore._();

  static const _storageKey = 'research_os_selected_provider_v1';
  static const defaultProvider = 'gemini';

  static Future<String> load() async {
    final prefs = await SharedPreferences.getInstance();
    final value = prefs.getString(_storageKey)?.trim();
    return value == null || value.isEmpty ? defaultProvider : value;
  }

  static Future<void> loadIntoState() async {
    selectedProviderState.value = await load();
  }

  static Future<void> save(String provider) async {
    final value = provider.trim();
    if (value.isEmpty) {
      throw const FormatException('Provider name must not be empty.');
    }
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_storageKey, value);
    selectedProviderState.value = value;
  }
}
