import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import 'identity_api_client.dart';
import 'owner_profile.dart';
import 'owner_profile_store.dart';

class OwnerSession {
  const OwnerSession({
    required this.email,
    required this.token,
    required this.expiresAt,
  });

  final String email;
  final String token;
  final DateTime expiresAt;

  bool get expired => DateTime.now().toUtc().isAfter(expiresAt);
}

final ValueNotifier<OwnerSession?> ownerSessionState =
    ValueNotifier<OwnerSession?>(null);

class OwnerSessionStore {
  OwnerSessionStore._();

  static const _storage = FlutterSecureStorage();
  static const _tokenKey = 'research_os_owner_session_token_v1';
  static const _emailKey = 'research_os_owner_session_email_v1';
  static const _expiresKey = 'research_os_owner_session_expires_v1';

  static Future<void> save({
    required String token,
    required String email,
    required DateTime expiresAt,
  }) async {
    final normalized = OwnerProfileStore.normalizeEmail(email);
    await _storage.write(key: _tokenKey, value: token);
    await _storage.write(key: _emailKey, value: normalized);
    await _storage.write(key: _expiresKey, value: expiresAt.toUtc().toIso8601String());
    ownerSessionState.value = OwnerSession(
      email: normalized,
      token: token,
      expiresAt: expiresAt.toUtc(),
    );
    await OwnerProfileStore.saveEmail(normalized);
  }

  static Future<void> clear({bool clearProfile = false}) async {
    await _storage.delete(key: _tokenKey);
    await _storage.delete(key: _emailKey);
    await _storage.delete(key: _expiresKey);
    ownerSessionState.value = null;
    if (clearProfile) await OwnerProfileStore.signOut();
  }

  static Future<OwnerSession?> loadLocal() async {
    final token = await _storage.read(key: _tokenKey);
    final email = await _storage.read(key: _emailKey);
    final expires = DateTime.tryParse(await _storage.read(key: _expiresKey) ?? '');
    if (token == null || email == null || expires == null) return null;
    final session = OwnerSession(
      email: email,
      token: token,
      expiresAt: expires.toUtc(),
    );
    if (session.expired) {
      await clear();
      return null;
    }
    return session;
  }

  static Future<OwnerSession?> restore({IdentityApiClient? api}) async {
    final session = await loadLocal();
    if (session == null) return null;
    final client = api ?? IdentityApiClient();
    try {
      final payload = await client.getProfile(session.token);
      final email = OwnerProfileStore.normalizeEmail(payload['email']?.toString() ?? '');
      if (email.isEmpty || email != session.email) {
        await clear();
        return null;
      }
      ownerSessionState.value = session;
      ownerProfileState.value = OwnerProfile(
        email: email,
        updatedAt: DateTime.now().toUtc(),
      );
      return session;
    } on IdentityApiException catch (error) {
      if (error.unauthorized) {
        await clear();
        return null;
      }
      ownerSessionState.value = session;
      return session;
    } on Object {
      // A network failure should not erase a still-valid verified session.
      ownerSessionState.value = session;
      return session;
    } finally {
      if (api == null) client.close();
    }
  }
}
