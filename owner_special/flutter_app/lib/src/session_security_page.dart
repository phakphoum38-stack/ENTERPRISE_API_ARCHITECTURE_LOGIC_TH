import 'package:flutter/material.dart';
import 'package:qr_flutter/qr_flutter.dart';

import 'owner_api.dart';

class SessionSecurityPage extends StatefulWidget {
  const SessionSecurityPage({required this.api, super.key});
  final OwnerFriendApi api;

  @override
  State<SessionSecurityPage> createState() => _SessionSecurityPageState();
}

class _SessionSecurityPageState extends State<SessionSecurityPage> {
  List<Map<String, dynamic>> _sessions = const <Map<String, dynamic>>[];
  String? _qrUri;
  String? _message;
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _refresh();
  }

  Future<void> _refresh() async {
    try {
      final sessions = await widget.api.authSessions();
      if (!mounted) return;
      setState(() {
        _sessions = sessions;
        _message = null;
      });
    } catch (error) {
      if (mounted) setState(() => _message = 'Session registry unavailable: $error');
    }
  }

  Future<void> _createQr() async {
    if (_busy) return;
    setState(() {
      _busy = true;
      _message = null;
      _qrUri = null;
    });
    try {
      final result = await widget.api.createQrHandoff();
      final uri = result['qr_uri']?.toString();
      if (uri == null || uri.isEmpty) {
        throw const FormatException('QR handoff response is incomplete');
      }
      if (!mounted) return;
      setState(() {
        _qrUri = uri;
        _message = 'One-time QR handoff created. It expires in ' + (result['ttl_seconds'] ?? 120).toString() + ' seconds.';
      });
    } catch (error) {
      if (mounted) setState(() => _message = 'QR handoff failed: $error');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _revoke(String sessionId) async {
    try {
      await widget.api.revokeAuthSession(sessionId);
      await _refresh();
    } catch (error) {
      if (mounted) setState(() => _message = 'Session revoke failed: $error');
    }
  }

  Future<void> _revokeAll() async {
    try {
      await widget.api.revokeAllAuthSessions();
      await _refresh();
    } catch (error) {
      if (mounted) setState(() => _message = 'Revoke-all failed: $error');
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return ListView(
      padding: const EdgeInsets.all(4),
      children: [
        Row(
          children: [
            Expanded(
              child: Text(
                'Session Security',
                style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w700),
              ),
            ),
            IconButton(
              tooltip: 'Refresh sessions',
              onPressed: _busy ? null : _refresh,
              icon: const Icon(Icons.refresh),
            ),
          ],
        ),
        Text(
          'Canonical Research OS sessions. Role and authorization remain server-derived.',
          style: theme.textTheme.bodyMedium?.copyWith(color: theme.colorScheme.onSurfaceVariant),
        ),
        const SizedBox(height: 16),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(18),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('QR / Native handoff', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
                const SizedBox(height: 6),
                Text('The QR contains only an opaque one-time handoff reference and audience. It never carries a session bearer, role, capability, command, or target.'),
                const SizedBox(height: 14),
                FilledButton.icon(
                  onPressed: _busy ? null : _createQr,
                  icon: _busy ? const SizedBox.square(dimension: 18, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.qr_code_2),
                  label: Text(_busy ? 'Creating…' : 'Create one-time QR'),
                ),
                if (_qrUri != null) ...[
                  const SizedBox(height: 18),
                  Center(
                    child: QrImageView(
                      data: _qrUri!,
                      size: 240,
                      backgroundColor: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 10),
                  SelectableText(_qrUri!, style: theme.textTheme.bodySmall),
                ],
                if (_message != null) ...[
                  const SizedBox(height: 10),
                  Text(_message!, style: theme.textTheme.bodySmall),
                ],
              ],
            ),
          ),
        ),
        const SizedBox(height: 16),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(18),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(child: Text('Active sessions', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700))),
                    TextButton(onPressed: _sessions.isEmpty ? null : _revokeAll, child: const Text('Revoke all')),
                  ],
                ),
                if (_sessions.isEmpty)
                  const Padding(
                    padding: EdgeInsets.symmetric(vertical: 18),
                    child: Text('No active sessions in the canonical registry.'),
                  )
                else
                  ..._sessions.map(
                    (session) => ListTile(
                      contentPadding: EdgeInsets.zero,
                      leading: Icon(session['current'] == true ? Icons.verified_user_outlined : Icons.devices_outlined),
                      title: Text(session['email']?.toString() ?? 'Research OS session'),
                      subtitle: Text(
                        (session['provider']?.toString() ?? 'native') +
                        ' • ' +
                        (session['role']?.toString() ?? 'user') +
                        ' • session ' +
                        (session['session_id']?.toString() ?? '-'),
                      ),
                      trailing: session['current'] == true
                          ? const Chip(label: Text('Current'))
                          : IconButton(
                              tooltip: 'Revoke session',
                              onPressed: () => _revoke(session['session_id']?.toString() ?? ''),
                              icon: const Icon(Icons.logout),
                            ),
                    ),
                  ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}
