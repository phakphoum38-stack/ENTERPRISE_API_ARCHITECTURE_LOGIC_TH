import 'package:flutter/material.dart';

import '../../identity/identity_api_client.dart';
import '../../identity/owner_profile.dart';
import '../../identity/owner_profile_store.dart';
import '../../identity/owner_session_store.dart';

class IdentitySettingsSection extends StatefulWidget {
  const IdentitySettingsSection({super.key});

  @override
  State<IdentitySettingsSection> createState() => _IdentitySettingsSectionState();
}

class _IdentitySettingsSectionState extends State<IdentitySettingsSection> {
  late final TextEditingController _emailController;
  late final TextEditingController _codeController;
  final IdentityApiClient _identityApi = IdentityApiClient();
  bool _busy = false;
  String? _challengeId;
  String? _error;

  @override
  void initState() {
    super.initState();
    _emailController = TextEditingController(
      text: ownerProfileState.value?.email ?? '',
    );
    _codeController = TextEditingController();
    ownerProfileState.addListener(_syncFromState);
    ownerSessionState.addListener(_syncFromState);
  }

  void _syncFromState() {
    final email = ownerProfileState.value?.email ?? ownerSessionState.value?.email ?? '';
    if (_emailController.text != email && email.isNotEmpty) {
      _emailController.text = email;
    }
    if (mounted) setState(() {});
  }

  @override
  void dispose() {
    ownerProfileState.removeListener(_syncFromState);
    ownerSessionState.removeListener(_syncFromState);
    _emailController.dispose();
    _codeController.dispose();
    _identityApi.close();
    super.dispose();
  }

  Future<void> _requestCode() async {
    if (_busy) return;
    final email = OwnerProfileStore.normalizeEmail(_emailController.text);
    if (!OwnerProfileStore.isValidEmail(email)) {
      setState(() => _error = 'กรุณาใส่อีเมลที่ถูกต้อง');
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final result = await _identityApi.requestCode(email);
      if (!mounted) return;
      setState(() {
        _challengeId = result['challenge_id']?.toString();
        _codeController.clear();
      });
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('ส่งรหัสยืนยันไปที่อีเมลแล้ว')),
      );
    } on Object catch (error) {
      if (!mounted) return;
      setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _verifyCode() async {
    if (_busy || _challengeId == null) return;
    final code = _codeController.text.trim();
    if (code.length != 6) {
      setState(() => _error = 'กรุณาใส่รหัส 6 หลัก');
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final result = await _identityApi.verifyCode(
        challengeId: _challengeId!,
        code: code,
      );
      final token = result['token']?.toString() ?? '';
      final expiresAtSeconds = result['expires_at'];
      final profile = result['profile'];
      final email = profile is Map<String, dynamic>
          ? profile['email']?.toString() ?? ''
          : _emailController.text;
      if (token.isEmpty || expiresAtSeconds is! num) {
        throw const IdentityApiException('Identity service did not return a valid session.');
      }
      final expiresAt = DateTime.fromMillisecondsSinceEpoch(
        expiresAtSeconds.toInt() * 1000,
        isUtc: true,
      );
      await OwnerSessionStore.save(
        token: token,
        email: email,
        expiresAt: expiresAt,
      );
      if (!mounted) return;
      setState(() {
        _challengeId = null;
        _codeController.clear();
      });
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('ยืนยันอีเมลสำเร็จ • Owner Session พร้อมใช้งาน')),
      );
    } on Object catch (error) {
      if (!mounted) return;
      setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _signOut() async {
    await OwnerSessionStore.clear(clearProfile: true);
    if (!mounted) return;
    setState(() {
      _challengeId = null;
      _emailController.clear();
      _codeController.clear();
    });
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('ออกจาก Owner Profile บนเครื่องนี้แล้ว')),
    );
  }

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<OwnerProfile?>(
      valueListenable: ownerProfileState,
      builder: (context, profile, _) {
        return ValueListenableBuilder<OwnerSession?>(
          valueListenable: ownerSessionState,
          builder: (context, session, __) {
            final verified = session != null && !session.expired;
            return Card(
              child: Padding(
                padding: const EdgeInsets.all(18),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Row(
                      children: <Widget>[
                        Icon(
                          verified
                              ? Icons.verified_user_outlined
                              : Icons.person_outline,
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            verified
                                ? 'Verified Owner • ${session.email}'
                                : profile == null
                                    ? 'General AI profile'
                                    : 'Local profile • ${profile.email}',
                            style: const TextStyle(fontWeight: FontWeight.w700),
                          ),
                        ),
                        Chip(
                          label: Text(
                            verified
                                ? 'Verified'
                                : profile == null
                                    ? 'General'
                                    : 'Local only',
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 14),
                    TextField(
                      key: const Key('owner-email-field'),
                      controller: _emailController,
                      enabled: !verified && !_busy,
                      keyboardType: TextInputType.emailAddress,
                      autocorrect: false,
                      enableSuggestions: false,
                      decoration: const InputDecoration(
                        labelText: 'Owner email',
                        hintText: 'name@example.com',
                        helperText:
                            'ยืนยันอีเมลเพื่อใช้ Owner Profile เดียวกันบนหลายเครื่อง',
                      ),
                    ),
                    if (_challengeId != null && !verified) ...<Widget>[
                      const SizedBox(height: 12),
                      TextField(
                        key: const Key('owner-verification-code-field'),
                        controller: _codeController,
                        enabled: !_busy,
                        keyboardType: TextInputType.number,
                        maxLength: 6,
                        decoration: const InputDecoration(
                          labelText: 'Verification code',
                          hintText: '000000',
                        ),
                        onSubmitted: (_) => _verifyCode(),
                      ),
                    ],
                    if (_error != null) ...<Widget>[
                      const SizedBox(height: 8),
                      Text(
                        _error!,
                        style: TextStyle(color: Theme.of(context).colorScheme.error),
                      ),
                    ],
                    const SizedBox(height: 12),
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: <Widget>[
                        if (!verified)
                          FilledButton.icon(
                            onPressed: _busy
                                ? null
                                : _challengeId == null
                                    ? _requestCode
                                    : _verifyCode,
                            icon: _busy
                                ? const SizedBox(
                                    width: 16,
                                    height: 16,
                                    child: CircularProgressIndicator(strokeWidth: 2),
                                  )
                                : Icon(
                                    _challengeId == null
                                        ? Icons.mail_outline
                                        : Icons.verified_outlined,
                                  ),
                            label: Text(
                              _challengeId == null
                                  ? 'ส่งรหัสยืนยัน'
                                  : 'ยืนยันรหัส',
                            ),
                          ),
                        if (_challengeId != null && !verified)
                          TextButton(
                            onPressed: _busy ? null : _requestCode,
                            child: const Text('ส่งรหัสใหม่'),
                          ),
                        if (verified || profile != null)
                          OutlinedButton.icon(
                            onPressed: _busy ? null : _signOut,
                            icon: const Icon(Icons.logout_outlined),
                            label: const Text('ออกจากโปรไฟล์บนเครื่องนี้'),
                          ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    const Divider(height: 1),
                    const SizedBox(height: 12),
                    Text(
                      verified
                          ? 'Owner Session ถูกเก็บใน secure storage ของอุปกรณ์และมีวันหมดอายุ '
                              'Cloud Profile sync ตอนนี้จำเฉพาะค่าทั่วไปของแอป; Private Context ยังไม่ถูกอัปโหลด.'
                          : 'หากไม่ยืนยันอีเมล Research OS จะทำงานเป็น AI ทั่วไปหรือ Local Profile เท่านั้น. '
                              'อีเมลอย่างเดียวไม่ถือว่าเป็นการยืนยันตัวตน.',
                    ),
                  ],
                ),
              ),
            );
          },
        );
      },
    );
  }
}
