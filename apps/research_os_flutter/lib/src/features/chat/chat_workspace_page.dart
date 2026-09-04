import 'package:flutter/material.dart';

import '../../api/research_os_api_client.dart';
import '../auth/google_login_page.dart';
import '../chat/voice_conversation_page.dart';
import 'chat_page.dart';

class ChatWorkspacePage extends StatelessWidget {
  const ChatWorkspacePage({required this.apiClient, super.key});

  final ResearchOSApiClient apiClient;

  static const List<_ChatTool> _tools = <_ChatTool>[
    _ChatTool('echo', 'Friend', 'พร้อมใช้', Icons.forum_outlined, true),
    _ChatTool('summarize', 'Friend', 'พร้อมใช้', Icons.summarize_outlined, true),
    _ChatTool('schedule.generate', 'Friend', 'พร้อมใช้', Icons.schedule_outlined, true),
    _ChatTool('web', 'V3', 'implemented', Icons.language_outlined, false),
    _ChatTool('github', 'V3', 'implemented', Icons.code_outlined, false),
    _ChatTool('file', 'V3', 'implemented', Icons.folder_open_outlined, false),
    _ChatTool('python', 'V3', 'implemented', Icons.data_object_outlined, false),
    _ChatTool('shell', 'V3', 'implemented', Icons.terminal_outlined, false),
    _ChatTool('github-actions', 'Repair', 'external', Icons.auto_fix_high_outlined, false),
    _ChatTool('github-repository', 'Repair', 'external', Icons.account_tree_outlined, false),
    _ChatTool('yaml-validator', 'Repair', 'พร้อมใช้', Icons.fact_check_outlined, true),
    _ChatTool('python-validator', 'Repair', 'พร้อมใช้', Icons.verified_outlined, true),
    _ChatTool('git-branch', 'Repair', 'พร้อมใช้', Icons.call_split_outlined, true),
    _ChatTool('pr-gate', 'Repair', 'พร้อมใช้', Icons.rule_outlined, true),
    _ChatTool('google-oauth', 'External', 'ต้องเชื่อมต่อ', Icons.login_outlined, false),
  ];

  Future<void> _showTools(BuildContext context) async {
    await showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      isScrollControlled: true,
      builder: (sheetContext) {
        return SafeArea(
          child: SizedBox(
            height: MediaQuery.sizeOf(sheetContext).height * 0.78,
            child: Column(
              children: <Widget>[
                Padding(
                  padding: const EdgeInsets.fromLTRB(20, 4, 20, 14),
                  child: Row(
                    children: <Widget>[
                      const Icon(Icons.build_circle_outlined),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: <Widget>[
                            Text(
                              'Research OS Tools',
                              style: Theme.of(sheetContext).textTheme.titleLarge,
                            ),
                            const Text('เครื่องมือที่ผูกกับ AI Workspace โดยตรง'),
                          ],
                        ),
                      ),
                      Text('${_tools.length} tools'),
                    ],
                  ),
                ),
                const Divider(height: 1),
                Expanded(
                  child: ListView.separated(
                    padding: const EdgeInsets.all(12),
                    itemCount: _tools.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 6),
                    itemBuilder: (context, index) {
                      final tool = _tools[index];
                      return Card(
                        margin: EdgeInsets.zero,
                        child: ListTile(
                          leading: CircleAvatar(child: Icon(tool.icon)),
                          title: Text(tool.name),
                          subtitle: Text('${tool.source} • ${tool.status}'),
                          trailing: tool.ready
                              ? const Icon(Icons.check_circle_outline)
                              : const Icon(Icons.more_horiz),
                          onTap: tool.name == 'google-oauth'
                              ? () {
                                  Navigator.pop(sheetContext);
                                  Navigator.of(context).push(
                                    MaterialPageRoute<void>(
                                      builder: (_) => GoogleLoginPage(apiClient: apiClient),
                                    ),
                                  );
                                }
                              : null,
                        ),
                      );
                    },
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  void _openVoice(BuildContext context) {
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => VoiceConversationPage(apiClient: apiClient),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: <Widget>[
        ChatPage(apiClient: apiClient),
        Positioned(
          right: 28,
          bottom: 76,
          child: SafeArea(
            child: Material(
              elevation: 8,
              borderRadius: BorderRadius.circular(18),
              color: Theme.of(context).colorScheme.surfaceContainerHighest,
              child: Padding(
                padding: const EdgeInsets.all(6),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: <Widget>[
                    IconButton(
                      key: const Key('chat-tools-button'),
                      tooltip: 'Tools',
                      onPressed: () => _showTools(context),
                      icon: const Icon(Icons.build_circle_outlined),
                    ),
                    IconButton(
                      key: const Key('chat-voice-button'),
                      tooltip: 'สนทนาด้วยเสียง',
                      onPressed: () => _openVoice(context),
                      icon: const Icon(Icons.mic_none_outlined),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class _ChatTool {
  const _ChatTool(this.name, this.source, this.status, this.icon, this.ready);

  final String name;
  final String source;
  final String status;
  final IconData icon;
  final bool ready;
}
