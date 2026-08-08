import 'package:flutter/material.dart';

import '../../identity/owner_profile.dart';
import '../../identity/owner_profile_store.dart';

class IdentitySettingsSection extends StatefulWidget {
  const IdentitySettingsSection({super.key});

  @override
  State<IdentitySettingsSection> createState() => _IdentitySettingsSectionState();
}

class _IdentitySettingsSectionState extends State<IdentitySettingsSection> {
  late final TextEditingController _emailController;
  bool _saving = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _emailController = TextEditingController(
      text: ownerProfileState.value?.email ?? '',
    );
    ownerProfileState.addListener(_syncFromState);
  }

  void _syncFromState() {
    final email = ownerProfileState.value?.email ?? '';
    if (_emailController.text != email) {
      _emailController.text = email;
    }
    if (mounted) setState(() {});
  }

  @override
  void dispose() {
    ownerProfileState.removeListener(_syncFromState);
    _emailController.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    if (_saving) return;
    setState(() {
      _saving = true;
      _error = null;
    });
    try {
      await OwnerProfileStore.saveEmail(_emailController.text);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('บันทึก Owner Profile แล้ว')),
      );
    } on Object catch (error) {
      if (!mounted) return;
      setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  Future<void> _signOut() async {
    await OwnerProfileStore.signOut();
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('ลบ Owner Profile ออกจากเครื่องนี้แล้ว')),
    );
  }

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<OwnerProfile?>(
      valueListenable: ownerProfileState,
      builder: (context, profile, _) {
        return Card(
          child: Padding(
            padding: const EdgeInsets.all(18),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Row(
                  children: <Widget>[
                    Icon(
                      profile == null
                          ? Icons.person_outline
                          : Icons.verified_user_outlined,
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        profile == null
                            ? 'General AI profile'
                            : 'Owner Profile • ${profile.email}',
                        style: const TextStyle(fontWeight: FontWeight.w700),
                      ),
                    ),
                    Chip(
                      label: Text(profile == null ? 'General' : 'Local profile'),
                    ),
                  ],
                ),
                const SizedBox(height: 14),
                TextField(
                  key: const Key('owner-email-field'),
                  controller: _emailController,
                  keyboardType: TextInputType.emailAddress,
                  autocorrect: false,
                  enableSuggestions: false,
                  decoration: const InputDecoration(
                    labelText: 'Owner email',
                    hintText: 'name@example.com',
                    helperText:
                        'ใช้เป็นตัวระบุโปรไฟล์บนเครื่องนี้ก่อน ระบบ Cloud verification จะเชื่อมในชั้น Auth ภายหลัง',
                  ),
                  onSubmitted: (_) => _save(),
                ),
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
                    FilledButton.icon(
                      onPressed: _saving ? null : _save,
                      icon: _saving
                          ? const SizedBox(
                              width: 16,
                              height: 16,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Icon(Icons.save_outlined),
                      label: const Text('จำอีเมลนี้'),
                    ),
                    if (profile != null)
                      OutlinedButton.icon(
                        onPressed: _saving ? null : _signOut,
                        icon: const Icon(Icons.logout_outlined),
                        label: const Text('ลบโปรไฟล์จากเครื่องนี้'),
                      ),
                  ],
                ),
                const SizedBox(height: 12),
                const Divider(height: 1),
                const SizedBox(height: 12),
                const Text(
                  'ข้อมูลอีเมลนี้เก็บใน local app storage และไม่ถูก commit ไป GitHub หรือฝังใน Release. '
                  'อีเมลอย่างเดียวจะไม่ถูกใช้เป็นหลักฐานยืนยันตัวตนสำหรับ Private Sync.',
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}
