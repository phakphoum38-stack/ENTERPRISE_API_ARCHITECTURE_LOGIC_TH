import 'package:flutter/material.dart';

import '../models/app_settings.dart';
import '../services/settings_service.dart';
import '../widgets/page_scaffold.dart';
import '../widgets/section_card.dart';

class SettingsPage extends StatefulWidget {
  const SettingsPage({super.key, required this.onChanged});
  final VoidCallback onChanged;

  @override
  State<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends State<SettingsPage> {
  final _service = SettingsService();
  final _owner = TextEditingController();
  final _root = TextEditingController();
  AppSettings _settings = const AppSettings();
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _owner.dispose();
    _root.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    final settings = await _service.load();
    if (!mounted) return;
    setState(() {
      _settings = settings;
      _owner.text = settings.githubOwner;
      _root.text = settings.preferredRootPath;
      _loading = false;
    });
  }

  Future<void> _save() async {
    final next = _settings.copyWith(githubOwner: _owner.text.trim(), preferredRootPath: _root.text.trim());
    await _service.save(next);
    if (!mounted) return;
    setState(() => _settings = next);
    widget.onChanged();
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('บันทึก Settings แล้ว')));
  }

  @override
  Widget build(BuildContext context) {
    return PageScaffold(
      title: 'Settings & Security',
      subtitle: 'ค่าควบคุมของ Research OS • secrets แยกจาก Drive เสมอ',
      actions: [FilledButton.icon(onPressed: _loading ? null : _save, icon: const Icon(Icons.save_outlined), label: const Text('บันทึก'))],
      child: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              children: [
                SectionCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('General', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
                      const SizedBox(height: 14),
                      TextField(controller: _owner, decoration: const InputDecoration(labelText: 'GitHub Owner')),
                      const SizedBox(height: 12),
                      TextField(controller: _root, decoration: const InputDecoration(labelText: 'Preferred Drive Root (เว้นว่าง = Auto Detect)')),
                      const SizedBox(height: 8),
                      SwitchListTile(contentPadding: EdgeInsets.zero, title: const Text('Auto Sync'), subtitle: const Text('ใช้ Scheduled Worker ที่ติดตั้งไว้'), value: _settings.autoSync, onChanged: (v) => setState(() => _settings = _settings.copyWith(autoSync: v))),
                    ],
                  ),
                ),
                const SizedBox(height: 12),
                const SectionCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Security Model', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
                      SizedBox(height: 10),
                      Text('• API keys: Windows DPAPI / CurrentUser / %LOCALAPPDATA%\\ResearchOS\\secrets\n• Provider metadata: %LOCALAPPDATA%\\ResearchOS\\config\n• Drive: source snapshots, bundles, logs, manifests\n• GitHub credentials: GitHub CLI credential store\n• Restore: local isolated workspace ก่อนนำไปใช้งานจริง', style: TextStyle(color: Colors.white70, height: 1.55)),
                    ],
                  ),
                ),
              ],
            ),
    );
  }
}
