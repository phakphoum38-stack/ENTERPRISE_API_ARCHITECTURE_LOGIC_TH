import 'package:flutter/material.dart';

import '../../api/research_os_api_client.dart';

class ApiLiveDemoPage extends StatefulWidget {
  const ApiLiveDemoPage({required this.apiClient, super.key});

  final ResearchOSApiClient apiClient;

  @override
  State<ApiLiveDemoPage> createState() => _ApiLiveDemoPageState();
}

class _ApiLiveDemoPageState extends State<ApiLiveDemoPage> {
  bool _loading = false;
  int? _statusCode;
  String _result = 'กดปุ่มเพื่อให้ Flutter ยิง API Platform';
  Duration? _latency;

  Future<void> _callHealth() async {
    final started = DateTime.now();
    setState(() { _loading = true; _statusCode = null; _result = 'กำลังยิง GET /health ...'; _latency = null; });
    try {
      final result = await widget.apiClient.getHealth();
      if (!mounted) return;
      setState(() { _statusCode = 200; _result = result.toString(); _latency = DateTime.now().difference(started); });
    } catch (error) {
      if (!mounted) return;
      setState(() { _result = error.toString(); _latency = DateTime.now().difference(started); });
    } finally { if (mounted) setState(() => _loading = false); }
  }

  Future<void> _callAi() async {
    final started = DateTime.now();
    setState(() { _loading = true; _statusCode = null; _result = 'กำลังยิง POST /v1/ai/generate ...'; _latency = null; });
    try {
      final result = await widget.apiClient.generateText('ตอบสั้น ๆ ว่า Flutter เชื่อมต่อ API Platform สำเร็จหรือไม่');
      if (!mounted) return;
      setState(() { _statusCode = 200; _result = result.toString(); _latency = DateTime.now().difference(started); });
    } catch (error) {
      if (!mounted) return;
      setState(() { _result = error.toString(); _latency = DateTime.now().difference(started); });
    } finally { if (mounted) setState(() => _loading = false); }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final success = _statusCode == 200;
    return Scaffold(
      appBar: AppBar(title: const Text('API Platform Live Demo')),
      body: ListView(
        padding: const EdgeInsets.all(24),
        children: [
          Card(child: Padding(padding: const EdgeInsets.all(24), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [Icon(Icons.api, color: scheme.primary, size: 32), const SizedBox(width: 12), const Expanded(child: Text('Flutter → API Platform', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800)))]),
            const SizedBox(height: 10),
            const Text('หน้านี้เป็นหลักฐานแบบมองเห็นได้ว่า Flutter ทำหน้าที่เป็น Consumer / Client และส่ง HTTP request ไปยัง API Platform โดยตรง'),
            const SizedBox(height: 20),
            Wrap(spacing: 12, runSpacing: 12, children: [
              FilledButton.icon(onPressed: _loading ? null : _callHealth, icon: const Icon(Icons.health_and_safety_outlined), label: const Text('GET /health')),
              OutlinedButton.icon(onPressed: _loading ? null : _callAi, icon: const Icon(Icons.psychology_outlined), label: const Text('POST /v1/ai/generate')),
            ]),
          ]))),
          const SizedBox(height: 16),
          Card(child: Padding(padding: const EdgeInsets.all(20), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('Request / Response', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 12),
            if (_loading) const LinearProgressIndicator(),
            const SizedBox(height: 12),
            Text(_statusCode == null ? 'STATUS: waiting' : 'STATUS: $_statusCode ${success ? '✓' : '✗'}', style: TextStyle(fontWeight: FontWeight.w800, color: success ? scheme.primary : scheme.error)),
            if (_latency != null) ...[const SizedBox(height: 4), Text('Latency: ${_latency!.inMilliseconds} ms')],
            const SizedBox(height: 12),
            SelectableText(_result),
          ]))),
        ],
      ),
    );
  }
}
