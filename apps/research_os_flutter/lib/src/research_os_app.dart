import 'dart:async';

import 'package:flutter/material.dart';

import 'api/api_auto_discovery.dart';
import 'api/api_connection_preferences.dart';
import 'api/api_connection_state.dart';
import 'api/api_endpoint_store.dart';
import 'api/provider_selection_store.dart';
import 'api/research_os_api_client.dart';
import 'app_shell.dart';
import 'identity/owner_cloud_sync.dart';
import 'identity/owner_profile_store.dart';
import 'identity/owner_session_store.dart';

class ResearchOSApp extends StatefulWidget {
  const ResearchOSApp({super.key});

  @override
  State<ResearchOSApp> createState() => _ResearchOSAppState();
}

class _ResearchOSAppState extends State<ResearchOSApp> {
  ThemeMode _themeMode = ThemeMode.system;
  ResearchOSApiClient? _apiClient;
  String? _apiBaseUrl;
  Timer? _heartbeatTimer;
  bool _reconnecting = false;
  ApiConnectionPreferences _connectionPreferences =
      ApiConnectionPreferences.defaults;

  @override
  void initState() {
    super.initState();
    apiConnectionPreferences.addListener(_handleConnectionPreferencesChanged);
    _initializeApp();
  }

  Future<void> _initializeApp() async {
    await ProviderSelectionStore.loadIntoState();
    await OwnerProfileStore.loadIntoState();
    await OwnerSessionStore.restore();
    await OwnerCloudSync.pullConnectionPreferences();
    await _loadApiEndpoint();
  }

  Future<void> _loadApiEndpoint() async {
    final preferences = await ApiConnectionPreferences.load();
    _connectionPreferences = preferences;
    apiConnectionPreferences.value = preferences;

    final preferred = await ApiEndpointStore.load();
    apiConnectionState.value = ApiConnectionSnapshot(
      phase: preferences.autoDiscovery
          ? ApiConnectionPhase.searching
          : ApiConnectionPhase.offline,
      baseUrl: preferred,
      source: preferences.autoDiscovery ? 'startup' : 'manual',
    );

    ApiDiscoveryResult? discovered;
    if (preferences.autoDiscovery) {
      discovered = await ApiAutoDiscovery.discover(
        preferredUrl: preferred,
        scanLan: preferences.scanLan,
      );
    } else {
      discovered = await ApiAutoDiscovery.probe(preferred, source: 'manual');
    }

    final url = discovered?.baseUrl ?? preferred;
    if (discovered != null && discovered.baseUrl != preferred) {
      await ApiEndpointStore.save(discovered.baseUrl);
    }
    if (!mounted) return;

    _replaceApiClient(url);
    apiConnectionState.value = ApiConnectionSnapshot(
      phase: discovered == null
          ? ApiConnectionPhase.offline
          : ApiConnectionPhase.connected,
      baseUrl: url,
      latency: discovered?.latency,
      source: discovered?.source ?? 'saved',
    );
    _startHeartbeat();
  }

  void _handleConnectionPreferencesChanged() {
    final next = apiConnectionPreferences.value;
    _connectionPreferences = next;
    _startHeartbeat();
    unawaited(OwnerCloudSync.pushConnectionPreferences(next));
    if (next.autoDiscovery) {
      unawaited(_verifyConnection(forceDiscovery: true));
    }
  }

  void _replaceApiClient(String url) {
    final previous = _apiClient;
    setState(() {
      _apiBaseUrl = url;
      _apiClient = ResearchOSApiClient(baseUrl: url);
    });
    previous?.close();
  }

  void _startHeartbeat() {
    _heartbeatTimer?.cancel();
    _heartbeatTimer = Timer.periodic(
      _connectionPreferences.heartbeatInterval,
      (_) => unawaited(_verifyConnection()),
    );
  }

  Future<void> _verifyConnection({bool forceDiscovery = false}) async {
    final current = _apiBaseUrl;
    if (current == null || _reconnecting) return;

    final healthy = await ApiAutoDiscovery.probe(current, source: 'heartbeat');
    if (healthy != null && !forceDiscovery) {
      apiConnectionState.value = ApiConnectionSnapshot(
        phase: ApiConnectionPhase.connected,
        baseUrl: healthy.baseUrl,
        latency: healthy.latency,
        source: healthy.source,
      );
      return;
    }

    if (!_connectionPreferences.autoDiscovery) {
      apiConnectionState.value = ApiConnectionSnapshot(
        phase: healthy == null
            ? ApiConnectionPhase.offline
            : ApiConnectionPhase.connected,
        baseUrl: current,
        latency: healthy?.latency,
        source: 'manual',
      );
      return;
    }

    if (!mounted) return;
    _reconnecting = true;
    apiConnectionState.value = ApiConnectionSnapshot(
      phase: ApiConnectionPhase.reconnecting,
      baseUrl: current,
      source: 'heartbeat',
    );
    try {
      final discovered = await ApiAutoDiscovery.discover(
        preferredUrl: current,
        scanLan: _connectionPreferences.scanLan,
      );
      if (!mounted) return;
      if (discovered == null) {
        apiConnectionState.value = ApiConnectionSnapshot(
          phase: ApiConnectionPhase.offline,
          baseUrl: current,
          source: 'none',
        );
        return;
      }

      if (discovered.baseUrl != current) {
        await ApiEndpointStore.save(discovered.baseUrl);
        if (!mounted) return;
        _replaceApiClient(discovered.baseUrl);
      }
      apiConnectionState.value = ApiConnectionSnapshot(
        phase: ApiConnectionPhase.connected,
        baseUrl: discovered.baseUrl,
        latency: discovered.latency,
        source: discovered.source,
      );
    } finally {
      _reconnecting = false;
    }
  }

  Future<void> _changeApiEndpoint(String value) async {
    final normalized = ApiEndpointStore.normalize(value);
    await ApiEndpointStore.save(normalized);
    if (!mounted) return;
    _replaceApiClient(normalized);
    apiConnectionState.value = ApiConnectionSnapshot(
      phase: ApiConnectionPhase.searching,
      baseUrl: normalized,
      source: 'manual',
    );
    unawaited(_verifyConnection());
  }

  ThemeData _buildTheme(Brightness brightness) {
    final dark = brightness == Brightness.dark;
    final scheme = ColorScheme.fromSeed(
      seedColor: const Color(0xFF1976D2),
      brightness: brightness,
      surface: dark ? const Color(0xFF101419) : const Color(0xFFF7F9FC),
    );

    final borderColor = dark
        ? Colors.white.withValues(alpha: .10)
        : Colors.black.withValues(alpha: .08);

    return ThemeData(
      useMaterial3: true,
      brightness: brightness,
      colorScheme: scheme,
      scaffoldBackgroundColor: dark
          ? const Color(0xFF0C1015)
          : const Color(0xFFF3F6FA),
      dividerColor: borderColor,
      appBarTheme: AppBarTheme(
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: false,
        backgroundColor: dark
            ? const Color(0xFF101419)
            : const Color(0xFFFDFEFF),
        surfaceTintColor: Colors.transparent,
        titleTextStyle: TextStyle(
          color: scheme.onSurface,
          fontSize: 18,
          fontWeight: FontWeight.w700,
        ),
      ),
      cardTheme: CardThemeData(
        elevation: 0,
        margin: EdgeInsets.zero,
        color: dark ? const Color(0xFF151A21) : Colors.white,
        surfaceTintColor: Colors.transparent,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: BorderSide(color: borderColor),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: dark ? const Color(0xFF151A21) : Colors.white,
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 13),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: borderColor),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: borderColor),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: scheme.primary, width: 1.4),
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 13),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 13),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          side: BorderSide(color: borderColor),
        ),
      ),
      chipTheme: ChipThemeData(
        side: BorderSide(color: borderColor),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      ),
      listTileTheme: ListTileThemeData(
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 2),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    );
  }

  @override
  void dispose() {
    apiConnectionPreferences.removeListener(_handleConnectionPreferencesChanged);
    _heartbeatTimer?.cancel();
    _apiClient?.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final apiClient = _apiClient;

    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Research OS',
      theme: _buildTheme(Brightness.light),
      darkTheme: _buildTheme(Brightness.dark),
      themeMode: _themeMode,
      home: apiClient == null || _apiBaseUrl == null
          ? const Scaffold(
              body: Center(child: CircularProgressIndicator()),
            )
          : ResearchOSAppShell(
              key: ValueKey(_apiBaseUrl),
              apiClient: apiClient,
              themeMode: _themeMode,
              onThemeModeChanged: (value) {
                setState(() => _themeMode = value);
              },
              onApiBaseUrlChanged: _changeApiEndpoint,
            ),
    );
  }
}
