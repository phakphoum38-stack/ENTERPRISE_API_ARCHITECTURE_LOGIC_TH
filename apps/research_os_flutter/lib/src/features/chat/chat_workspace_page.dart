import 'package:flutter/material.dart';

import '../../api/research_os_api_client.dart';
import 'voice_conversation_page.dart';

class ChatWorkspacePage extends StatefulWidget {
  const ChatWorkspacePage({required this.apiClient, super.key});
  final ResearchOSApiClient apiClient;

  @override
  State<ChatWorkspacePage> createState() => _ChatWorkspacePageState();
}

class _ChatWorkspacePageState extends State<ChatWorkspacePage> {
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scroll = ScrollController();
  final List<_Turn> _turns = <_Turn>[];
  final Set<String> _tools = <String>{};
  bool _memory = true;
  bool _sending = false;
  String? _error;

  static const _availableTools = <String>['Web', 'GitHub', 'Files', 'Python', 'Shell'];

  @override
  void dispose() {
    _controller.dispose();
    _scroll.dispose();
    super.dispose();
  }

  Future<void> _send() async {
    final prompt = _controller.text.trim();
    if (prompt.isEmpty || _sending) return;
    final request = _tools.isEmpty ? prompt : '$prompt\n\nTools selected: ${_tools.join(', ')}';
    setState(() {
      _turns.add(_Turn('user', prompt));
      _controller.clear();
      _sending = true;
      _error = null;
    });
    await _scrollBottom();
    try {
      final response = _memory
          ? await widget.apiClient.answerWithMemory(request)
          : await widget.apiClient.generateText(request);
      final text = (response['text'] ?? response['answer'] ?? '').toString().trim();
      if (!mounted) return;
      setState(() => _turns.add(_Turn('assistant', text.isEmpty ? 'ไม่ได้รับข้อความตอบกลับจาก Friend AI' : text)));
      await _scrollBottom();
    } on Object catch (error) {
      if (mounted) setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  Future<void> _scrollBottom() async {
    await Future<void>.delayed(const Duration(milliseconds: 30));
    if (!_scroll.hasClients) return;
    await _scroll.animateTo(_scroll.position.maxScrollExtent, duration: const Duration(milliseconds: 180), curve: Curves.easeOut);
  }

  void _openVoice() {
    Navigator.of(context).push(MaterialPageRoute<void>(builder: (_) => VoiceConversationPage(apiClient: widget.apiClient)));
  }

  void _showToolCenter() {
    showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      builder: (context) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Wrap(
            spacing: 10,
            runSpacing: 10,
            children: _availableTools.map((tool) => FilterChip(
              selected: _tools.contains(tool),
              label: Text(tool),
              onSelected: (selected) => setState(() => selected ? _tools.add(tool) : _tools.remove(tool)),
            )).toList(),
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 20, 20, 14),
          child: Column(
            children: <Widget>[
              Row(children: <Widget>[
                Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: <Widget>[
                  Text('สนทนา AI', style: Theme.of(context).textTheme.headlineSmall),
                  const SizedBox(height: 4),
                  const Text('Friend AI • Text + Voice • Research OS Workspace'),
                ])),
                IconButton(tooltip: 'Voice Conversation', onPressed: _openVoice, icon: const Icon(Icons.mic_none_outlined)),
                IconButton(tooltip: 'Tool Center', onPressed: _showToolCenter, icon: const Icon(Icons.build_outlined)),
              ]),
              const SizedBox(height: 12),
              Card(margin: EdgeInsets.zero, child: Padding(padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10), child: Wrap(spacing: 8, runSpacing: 8, children: <Widget>[
                FilterChip(selected: _memory, avatar: const Icon(Icons.memory_outlined, size: 17), label: const Text('Memory'), onSelected: _sending ? null : (v) => setState(() => _memory = v)),
                ..._availableTools.map((tool) => FilterChip(selected: _tools.contains(tool), label: Text(tool), onSelected: _sending ? null : (v) => setState(() => v ? _tools.add(tool) : _tools.remove(tool)))),
              ]))),
              if (_error != null) ...<Widget>[
                const SizedBox(height: 10),
                ListTile(tileColor: scheme.errorContainer, leading: Icon(Icons.error_outline, color: scheme.onErrorContainer), title: Text('AI Workspace error', style: TextStyle(color: scheme.onErrorContainer)), subtitle: Text(_error!, style: TextStyle(color: scheme.onErrorContainer)), trailing: IconButton(onPressed: () => setState(() => _error = null), icon: const Icon(Icons.close))),
              ],
              const SizedBox(height: 12),
              Expanded(child: Card(margin: EdgeInsets.zero, clipBehavior: Clip.antiAlias, child: _turns.isEmpty
                ? Center(child: SingleChildScrollView(padding: const EdgeInsets.all(32), child: Column(mainAxisSize: MainAxisSize.min, children: <Widget>[
                    Icon(Icons.auto_awesome, size: 64, color: scheme.primary),
                    const SizedBox(height: 16),
                    Text('เริ่มสนทนากับ Friend AI', style: Theme.of(context).textTheme.headlineSmall),
                    const SizedBox(height: 8),
                    const Text('พิมพ์ข้อความด้านล่าง หรือกดไมโครโฟนเพื่อสนทนาด้วยเสียง\nเลือก Memory และเครื่องมือที่ต้องการใช้กับบทสนทนาได้ทันที', textAlign: TextAlign.center),
                  ])))
                : ListView.builder(controller: _scroll, padding: const EdgeInsets.all(20), itemCount: _turns.length, itemBuilder: (context, index) {
                    final turn = _turns[index];
                    final user = turn.role == 'user';
                    return Align(alignment: user ? Alignment.centerRight : Alignment.centerLeft, child: Container(constraints: const BoxConstraints(maxWidth: 760), margin: const EdgeInsets.only(bottom: 12), padding: const EdgeInsets.all(16), decoration: BoxDecoration(color: user ? scheme.primaryContainer : scheme.surfaceContainer, borderRadius: BorderRadius.circular(18)), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: <Widget>[Text(user ? 'คุณ' : 'Friend AI', style: Theme.of(context).textTheme.labelLarge), const SizedBox(height: 6), SelectableText(turn.text)])));
                  }))),
              const SizedBox(height: 12),
              Card(margin: EdgeInsets.zero, child: Padding(padding: const EdgeInsets.fromLTRB(8, 6, 8, 6), child: Row(crossAxisAlignment: CrossAxisAlignment.end, children: <Widget>[
                IconButton(tooltip: 'Voice Conversation', onPressed: _sending ? null : _openVoice, icon: const Icon(Icons.mic_none)),
                Expanded(child: TextField(controller: _controller, minLines: 1, maxLines: 6, textInputAction: TextInputAction.newline, onSubmitted: (_) => _send(), decoration: InputDecoration(hintText: _tools.isEmpty ? 'พิมพ์ข้อความถึง Friend AI…' : 'พิมพ์คำสั่งถึง Friend AI (${_tools.join(', ')})…', border: InputBorder.none))),
                IconButton.filled(tooltip: 'ส่งข้อความ', onPressed: _sending ? null : _send, icon: _sending ? const SizedBox(width: 19, height: 19, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.arrow_upward)),
              ]))),
            ],
          ),
        ),
      ),
    );
  }
}

class _Turn {
  const _Turn(this.role, this.text);
  final String role;
  final String text;
}
