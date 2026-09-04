import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';

import 'owner_api.dart';

class GoogleIdentityPage extends StatefulWidget {
  const GoogleIdentityPage({required this.api, super.key});
  final OwnerFriendApi api;

  @override
  State<GoogleIdentityPage> createState() => _GoogleIdentityPageState();
}

class _GoogleIdentityPageState extends State<GoogleIdentityPage> {
  Timer? _poller;
  bool _busy = false;
  String? _email;
  String? _role;
  String? _message;

  @override
  void initState() {
    super.initState();
    _refresh();
  }

  @override
  void dispose() {
    _poller?.cancel();
    super.dispose();
  }

  Future<void> _refresh() async {
    try {
      final result = await widget.api.authStatus();
      final account = result['account'];
      if (!mounted) return;
      setState(() {
        _email = account is Map ? account['email']?.toString() : null;
        _role = account is Map ? account['role']?.toString() : null;
        _message = null;
      });
    } catch (error) {
      if (!mounted) return;
      setState(() => _message = 'Research OS identity service unavailable: $error');
    }
  }

  Future<void> _signIn() async {
    if (_busy) return;
    setState(() {
      _busy = true;
      _message = null;
    });
    try {
      final result = await widget.api.startGoogleIdentity();
      final url = result['authorization_url']?.toString();
      final state = result['state']?.toString();
      if (url == null || url.isEmpty || state == null || state.isEmpty) {
        throw const FormatException('Google authorization response is incomplete');
      }
      if (!Platform.isWindows) {
        throw const UnsupportedError('Native Google sign-in is currently enabled for Windows desktop.');
      }
      await Process.run('cmd', ['/c', 'start', '', url]);
      _poller?.cancel();
      var attempts = 0;
      _poller = Timer.periodic(const Duration(seconds: 2), (timer) async {
        attempts++;
        if (attempts > 60) {
          timer.cancel();
          if (mounted) setState(() => _message = 'Google sign-in timed out.');
          return;
        }
        try {
          final handoff = await widget.api.exchangeGoogleIdentityHandoff(state);
          final token = handoff['session']?.toString();
          final account = handoff['account'];
          if (token == null || token.isEmpty) return;
          timer.cancel();
          widget.api.setSession(token);
          if (!mounted) return;
          setState(() {
            _email = account is Map ? account['email']?.toString() : null;
            _role = account is Map ? account['role']?.toString() : null;
            _message = 'Google Identity connected';
            _busy = false;
          });
        } catch (_) {
          // The callback may not have completed yet; keep polling the one-time handoff.
        }
      });
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _busy = false;
        _message = error.toString();
      });
    }
  }

  Future<void> _signOut() async {
    setState(() => _busy = true);
    try {
      await widget.api.signOut();
    } finally {
      widget.api.clearSession();
      _poller?.cancel();
      if (mounted) {
        setState(() {
          _busy = false;
          _email = null;
          _role = null;
          _message = 'Signed out';
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final connected = _email != null && _email!.isNotEmpty;
    return ListView(
      padding: const EdgeInsets.all(4),
      children: [
        Text('Google Identity', style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w700)),
        const SizedBox(height: 6),
        Text('Research OS account and session', style: theme.textTheme.bodyMedium?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
        const SizedBox(height: 20),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    CircleAvatar(
                      radius: 24,
                      child: Icon(connected ? Icons.verified_user_outlined : Icons.account_circle_outlined),
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(connected ? 'Connected' : 'Not connected', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
                          const SizedBox(height: 3),
                          Text(connected ? _email! : 'Sign in with Google to activate your Research OS workspace session'),
                        ],
                      ),
                    ),
                    if (connected)
                      FilledButton.tonalIcon(onPressed: _busy ? null : _signOut, icon: const Icon(Icons.logout), label: const Text('Sign out'))
                    else
                      FilledButton.icon(onPressed: _busy ? null : _signIn, icon: const Icon(Icons.login), label: Text(_busy ? 'Waiting…' : 'Sign in with Google')),
                  ],
                ),
                if (connected && _role != null) ...[
                  const SizedBox(height: 16),
                  Wrap(spacing: 8, children: [Chip(label: Text('Role: $_role')), const Chip(label: Text('Signed Research OS session'))]),
                ],
                if (_message != null) ...[
                  const SizedBox(height: 14),
                  Text(_message!, style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
                ],
              ],
            ),
          ),
        ),
      ],
    );
  }
}
