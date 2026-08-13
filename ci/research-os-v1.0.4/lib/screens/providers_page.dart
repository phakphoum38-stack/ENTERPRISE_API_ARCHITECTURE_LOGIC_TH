import 'package:flutter/material.dart';

import '../models/provider_profile.dart';
import '../services/provider_service.dart';
import '../widgets/page_scaffold.dart';
import '../widgets/section_card.dart';

class ProvidersPage extends StatefulWidget {
  const ProvidersPage({super.key});

  @override
  State<ProvidersPage> createState() => _ProvidersPageState();
}

class _ProvidersPageState extends State<ProvidersPage> {
  final _service = ProviderService();
  List<ProviderProfile> _providers = const [];
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _reload();
  }

  Future<void> _reload() async {
    final items = await _service.loadProviders();
    if (mounted) setState(() => _providers = items);
  }

  Future<void> _edit([ProviderProfile? current]) async {
    final name = TextEditingController(text: current?.name ?? 'OpenAI-compatible');
    final base = TextEditingController(text: current?.baseUrl ?? 'http://127.0.0.1:8000/v1');
    final model = TextEditingController(text: current?.model ?? 'default');
    final secret = TextEditingController();
    var enabled = current?.enabled ?? true;

    final result = await showDialog<bool>(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setLocal) => AlertDialog(
          title: Text(current == null ? 'เพิ่ม API Provider' : 'แก้ไข ${current.name}'),
          content: SizedBox(
            width: 520,
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  TextField(controller: name, decoration: const InputDecoration(labelText: 'ชื่อ Provider')),
                  const SizedBox(height: 12),
                  TextField(controller: base, decoration: const InputDecoration(labelText: 'Base URL เช่น http://127.0.0.1:8000/v1')),
                  const SizedBox(height: 12),
                  TextField(controller: model, decoration: const InputDecoration(labelText: 'Model')),
                  const SizedBox(height: 12),
                  TextField(controller: secret, obscureText: true, decoration: InputDecoration(labelText: current?.keyStored == true ? 'API Key ใหม่ (เว้นว่างเพื่อใช้ของเดิม)' : 'API Key (เว้นว่างได้สำหรับ local provider)')),
                  const SizedBox(height: 8),
                  SwitchListTile(contentPadding: EdgeInsets.zero, value: enabled, onChanged: (v) => setLocal(() => enabled = v), title: const Text('เปิดใช้งาน Provider')),
                ],
              ),
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('ยกเลิก')),
            FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('บันทึก')),
          ],
        ),
      ),
    );

    if (result != true) return;
    final id = current?.id ?? _slug('${name.text}-${DateTime.now().millisecondsSinceEpoch}');
    await _run(() => _service.upsertProvider(
          ProviderProfile(id: id, name: name.text.trim(), baseUrl: base.text.trim(), model: model.text.trim(), enabled: enabled, keyStored: current?.keyStored ?? false),
          secret: secret.text,
        ));
  }

  Future<void> _run(Future<void> Function() action) async {
    setState(() => _busy = true);
    try {
      await action();
      await _reload();
    } catch (e) {
      if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$e')));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return PageScaffold(
      title: 'API Providers',
      subtitle: 'เก็บ metadata ในเครื่อง และ API key ด้วย Windows DPAPI • ไม่ sync secret เข้า Drive',
      actions: [FilledButton.icon(onPressed: _busy ? null : () => _edit(), icon: const Icon(Icons.add), label: const Text('เพิ่ม Provider'))],
      child: _providers.isEmpty
          ? const SectionCard(child: Center(child: Padding(padding: EdgeInsets.all(40), child: Text('ยังไม่มี Provider'))))
          : ListView.separated(
              itemCount: _providers.length,
              separatorBuilder: (_, __) => const SizedBox(height: 10),
              itemBuilder: (itemContext, index) {
                final p = _providers[index];
                return SectionCard(
                  child: Row(
                    children: [
                      CircleAvatar(child: Icon(p.enabled ? Icons.smart_toy : Icons.smart_toy_outlined)),
                      const SizedBox(width: 14),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(children: [Text(p.name, style: const TextStyle(fontWeight: FontWeight.w700)), const SizedBox(width: 8), _Badge(text: p.enabled ? 'ON' : 'OFF', good: p.enabled), if (p.keyStored) ...[const SizedBox(width: 6), const _Badge(text: 'KEY STORED', good: true)]]),
                            const SizedBox(height: 4),
                            Text('${p.baseUrl} • ${p.model}', style: const TextStyle(color: Colors.white60)),
                          ],
                        ),
                      ),
                      IconButton(onPressed: _busy ? null : () async {
                        try {
                          final message = await _service.testProvider(p);
                          if (itemContext.mounted) {
                            ScaffoldMessenger.of(itemContext).showSnackBar(SnackBar(content: Text(message)));
                          }
                        } catch (e) {
                          if (itemContext.mounted) {
                            ScaffoldMessenger.of(itemContext).showSnackBar(SnackBar(content: Text('ทดสอบไม่ผ่าน: $e')));
                          }
                        }
                      }, tooltip: 'ทดสอบการเชื่อมต่อ', icon: const Icon(Icons.wifi_tethering)),
                      IconButton(onPressed: _busy ? null : () => _edit(p), tooltip: 'แก้ไข', icon: const Icon(Icons.edit_outlined)),
                      IconButton(onPressed: _busy ? null : () => _run(() => _service.deleteProvider(p.id)), tooltip: 'ลบ', icon: const Icon(Icons.delete_outline)),
                    ],
                  ),
                );
              },
            ),
    );
  }

  String _slug(String value) => value.toLowerCase().replaceAll(RegExp(r'[^a-z0-9]+'), '-').replaceAll(RegExp(r'^-|-$'), '');
}

class _Badge extends StatelessWidget {
  const _Badge({required this.text, required this.good});
  final String text;
  final bool good;

  @override
  Widget build(BuildContext context) {
    final color = good ? Colors.greenAccent : Colors.orangeAccent;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(color: color.withValues(alpha: .1), borderRadius: BorderRadius.circular(999), border: Border.all(color: color.withValues(alpha: .3))),
      child: Text(text, style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.w700)),
    );
  }
}
