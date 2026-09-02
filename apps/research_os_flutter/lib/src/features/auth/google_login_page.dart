import 'dart:async';

import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../api/research_os_api_client.dart';

class GoogleLoginPage extends StatefulWidget {
  const GoogleLoginPage({required this.apiClient, super.key});

  final ResearchOSApiClient apiClient;

  @override
  State<GoogleLoginPage> createState() => _GoogleLoginPageState();
}

class _GoogleLoginPageState extends State<GoogleLoginPage> {
  bool _busy = false;
  String? _message;
  bool _error = false;

  Future<void> _continueWithGoogle() async {
    if (_busy) return;
    setState(() {
      _busy = true;
      _message = null;
      _error = false;
    });

    try {
      final response = await widget.apiClient.startGoogleIdentitySignIn();
      final rawUrl = response['authorization_url']?.toString().trim();
      if (rawUrl == null || rawUrl.isEmpty) {
        throw const ResearchOSApiException(
          'Research OS ไม่ได้รับ Google authorization URL',
        );
      }
      final uri = Uri.tryParse(rawUrl);
      if (uri == null || !uri.hasScheme) {
        throw const ResearchOSApiException('Google authorization URL ไม่ถูกต้อง');
      }
      final state = uri.queryParameters['state']?.trim();
      if (state == null || state.isEmpty) {
        throw const ResearchOSApiException('Google authorization URL ไม่มี OAuth state');
      }

      final opened = await launchUrl(
        uri,
        mode: LaunchMode.externalApplication,
      );
      if (!opened) {
        throw const ResearchOSApiException('เปิดหน้า Google Sign-In ไม่สำเร็จ');
      }

      if (mounted) {
        setState(() {
          _message = 'เปิด Google Sign-In แล้ว กรุณาทำรายการในเบราว์เซอร์ให้เสร็จ…';
        });
      }

      final authenticated = await _waitForDesktopSession(state);
      if (!authenticated) {
        throw const ResearchOSApiException(
          'Google Sign-In ยังไม่เสร็จภายในเวลาที่กำหนด กรุณาลองใหม่',
        );
      }

      if (!mounted) return;
      setState(() {
        _message = 'เข้าสู่ระบบ Research OS สำเร็จแล้ว';
        _error = false;
      });
    } on Object catch (error) {
      if (!mounted) return;
      setState(() {
        _error = true;
        _message = error.toString();
      });
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<bool> _waitForDesktopSession(String state) async {
    for (var attempt = 0; attempt < 60; attempt++) {
      await Future<void>.delayed(const Duration(seconds: 2));
      if (!mounted) return false;
      try {
        final status = await widget.apiClient.getAuthStatusForOAuthState(state);
        if (status['connected'] == true) {
          final token = status['session']?.toString().trim();
          if (token != null && token.isNotEmpty) {
            widget.apiClient.setSessionToken(token);
            return true;
          }
        }
      } on Object {
        // OAuth browser completion and API polling are independent. Transient
        // network failures should not abort a sign-in that is still running.
      }
    }
    return false;
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;

    return Scaffold(
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 520),
          child: Padding(
            padding: const EdgeInsets.all(28),
            child: Card(
              child: Padding(
                padding: const EdgeInsets.all(32),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: <Widget>[
                    Container(
                      width: 72,
                      height: 72,
                      alignment: Alignment.center,
                      decoration: BoxDecoration(
                        color: scheme.primaryContainer,
                        borderRadius: BorderRadius.circular(22),
                      ),
                      child: Icon(
                        Icons.account_circle_outlined,
                        size: 42,
                        color: scheme.onPrimaryContainer,
                      ),
                    ),
                    const SizedBox(height: 22),
                    Text(
                      'Research OS',
                      style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                            fontWeight: FontWeight.w800,
                          ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Your intelligent research workspace',
                      textAlign: TextAlign.center,
                      style: Theme.of(context).textTheme.bodyLarge,
                    ),
                    const SizedBox(height: 28),
                    SizedBox(
                      width: double.infinity,
                      child: FilledButton.icon(
                        onPressed: _busy ? null : _continueWithGoogle,
                        icon: _busy
                            ? const SizedBox(
                                width: 18,
                                height: 18,
                                child: CircularProgressIndicator(strokeWidth: 2),
                              )
                            : const Icon(Icons.login),
                        label: Text(
                          _busy ? 'กำลังยืนยัน Google…' : 'Continue with Google',
                        ),
                      ),
                    ),
                    const SizedBox(height: 18),
                    Text(
                      'ใช้สำหรับ Research OS identity/session เท่านั้น\nไม่ขอสิทธิ์ Google Calendar, Drive หรือ Gmail',
                      textAlign: TextAlign.center,
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                    if (_message != null) ...<Widget>[
                      const SizedBox(height: 18),
                      Text(
                        _message!,
                        textAlign: TextAlign.center,
                        style: TextStyle(color: _error ? scheme.error : scheme.primary),
                      ),
                    ],
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
