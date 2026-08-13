import 'package:flutter/material.dart';

import '../models/chat_conversation.dart';
import '../models/chat_message.dart';
import '../models/provider_profile.dart';
import '../services/chat_service.dart';
import '../services/chat_store_service.dart';
import '../services/provider_service.dart';
import '../widgets/page_scaffold.dart';
import '../widgets/section_card.dart';

class ChatPage extends StatefulWidget {
  const ChatPage({super.key});

  @override
  State<ChatPage> createState() => _ChatPageState();
}

class _ChatPageState extends State<ChatPage> {
  final _providerService = ProviderService();
  final _store = ChatStoreService();
  late final ChatService _chatService = ChatService(_providerService);
  final _controller = TextEditingController();
  final _conversationSearch = TextEditingController();
  final _scroll = ScrollController();

  List<ProviderProfile> _providers = const [];
  List<ChatConversation> _conversations = const [];
  final _messages = <ChatMessage>[];
  String? _providerId;
  String? _conversationId;
  bool _sending = false;
  bool _showArchived = false;
  String _streaming = '';
  int _generation = 0;

  @override
  void initState() {
    super.initState();
    _initialize();
  }

  @override
  void dispose() {
    _controller.dispose();
    _conversationSearch.dispose();
    _scroll.dispose();
    super.dispose();
  }

  Future<void> _initialize() async {
    await Future.wait([_loadProviders(), _loadConversations()]);
  }

  Future<void> _loadProviders() async {
    final providers = await _providerService.loadProviders();
    if (!mounted) return;
    final enabled = providers.where((p) => p.enabled).toList();
    setState(() {
      _providers = enabled;
      if (_providerId == null || !enabled.any((p) => p.id == _providerId)) {
        _providerId = enabled.isNotEmpty ? enabled.first.id : null;
      }
    });
  }

  Future<void> _loadConversations() async {
    var items = await _store.listConversations();
    if (items.isEmpty) {
      final created = await _store.createConversation();
      items = [created];
    }
    if (!mounted) return;
    setState(() {
      _conversations = items;
      final current = items.where((c) => c.id == _conversationId).firstOrNull ?? items.first;
      _conversationId = current.id;
      _messages
        ..clear()
        ..addAll(current.messages);
    });
    _jumpToBottom();
  }

  ChatConversation? get _currentConversation => _conversations.where((c) => c.id == _conversationId).firstOrNull;

  Future<void> _selectConversation(ChatConversation conversation) async {
    _generation++;
    setState(() {
      _conversationId = conversation.id;
      _messages
        ..clear()
        ..addAll(conversation.messages);
      _streaming = '';
      _sending = false;
    });
    _jumpToBottom();
  }

  Future<void> _newConversation() async {
    final created = await _store.createConversation();
    await _loadConversations();
    final match = _conversations.where((c) => c.id == created.id).firstOrNull;
    if (match != null) await _selectConversation(match);
  }

  Future<void> _persistCurrent({String? autoTitle}) async {
    final current = _currentConversation;
    if (current == null) return;
    var title = current.title;
    if (autoTitle != null && title == 'New Chat') {
      final clean = autoTitle.replaceAll(RegExp(r'\s+'), ' ').trim();
      title = clean.length > 42 ? '${clean.substring(0, 42)}…' : clean;
    }
    final updated = current.copyWith(
      title: title,
      updatedAt: DateTime.now(),
      messages: List<ChatMessage>.from(_messages),
    );
    await _store.save(updated);
    final index = _conversations.indexWhere((c) => c.id == updated.id);
    if (index >= 0 && mounted) {
      setState(() {
        final next = List<ChatConversation>.from(_conversations);
        next[index] = updated;
        next.sort((a, b) => b.updatedAt.compareTo(a.updatedAt));
        _conversations = next;
      });
    }
  }

  Future<void> _rename(ChatConversation conversation) async {
    final controller = TextEditingController(text: conversation.title);
    final ok = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('เปลี่ยนชื่อแชต'),
        content: TextField(controller: controller, autofocus: true, decoration: const InputDecoration(labelText: 'ชื่อ')),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('ยกเลิก')),
          FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('บันทึก')),
        ],
      ),
    );
    if (ok != true || controller.text.trim().isEmpty) return;
    await _store.save(conversation.copyWith(title: controller.text.trim(), updatedAt: DateTime.now()));
    await _loadConversations();
  }

  Future<void> _toggleArchive(ChatConversation conversation) async {
    await _store.save(conversation.copyWith(archived: !conversation.archived, updatedAt: DateTime.now()));
    await _loadConversations();
  }

  Future<void> _deleteConversation(ChatConversation conversation) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('ลบแชต?'),
        content: Text('ลบ “${conversation.title}” จากเครื่องนี้'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('ยกเลิก')),
          FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('ลบ')),
        ],
      ),
    );
    if (ok != true) return;
    await _store.delete(conversation.id);
    _conversationId = null;
    await _loadConversations();
  }

  Future<void> _send() async {
    final text = _controller.text.trim();
    final provider = _providers.where((p) => p.id == _providerId).firstOrNull;
    if (text.isEmpty || provider == null || _sending) return;

    final token = ++_generation;
    setState(() {
      _messages.add(ChatMessage(role: ChatRole.user, content: text, createdAt: DateTime.now()));
      _controller.clear();
      _sending = true;
      _streaming = '';
    });
    await _persistCurrent(autoTitle: text);
    _jumpToBottom();

    try {
      await for (final chunk in _chatService.streamCompletion(provider: provider, messages: _messages)) {
        if (!mounted || token != _generation) break;
        setState(() => _streaming += chunk);
        _jumpToBottom();
      }
      if (!mounted || token != _generation) return;
      if (_streaming.trim().isNotEmpty) {
        setState(() {
          _messages.add(ChatMessage(role: ChatRole.assistant, content: _streaming, createdAt: DateTime.now()));
          _streaming = '';
        });
        await _persistCurrent();
      }
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('AI request failed: $e')));
    } finally {
      if (mounted && token == _generation) setState(() => _sending = false);
    }
  }

  void _stop() {
    setState(() {
      _generation++;
      _sending = false;
      if (_streaming.trim().isNotEmpty) {
        _messages.add(ChatMessage(role: ChatRole.assistant, content: _streaming, createdAt: DateTime.now()));
        _streaming = '';
      }
    });
    _persistCurrent();
  }

  void _jumpToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_scroll.hasClients) return;
      _scroll.animateTo(_scroll.position.maxScrollExtent, duration: const Duration(milliseconds: 180), curve: Curves.easeOut);
    });
  }

  Future<void> _showChatsDialog() async {
    await showDialog<void>(
      context: context,
      builder: (dialogContext) => StatefulBuilder(
        builder: (dialogContext, setDialog) => Dialog(
          child: SizedBox(
            width: 440,
            height: 620,
            child: Padding(
              padding: const EdgeInsets.all(14),
              child: _ConversationPanel(
                conversations: _filteredConversations(),
                currentId: _conversationId,
                searchController: _conversationSearch,
                showArchived: _showArchived,
                onSearch: () { setState(() {}); setDialog(() {}); },
                onToggleArchived: (v) { setState(() => _showArchived = v); setDialog(() {}); },
                onNew: () async { Navigator.pop(dialogContext); await _newConversation(); },
                onSelect: (c) async { Navigator.pop(dialogContext); await _selectConversation(c); },
                onRename: (c) async { await _rename(c); setDialog(() {}); },
                onArchive: (c) async { await _toggleArchive(c); setDialog(() {}); },
                onDelete: (c) async { await _deleteConversation(c); if (dialogContext.mounted) setDialog(() {}); },
              ),
            ),
          ),
        ),
      ),
    );
  }

  List<ChatConversation> _filteredConversations() {
    final q = _conversationSearch.text.trim().toLowerCase();
    return _conversations.where((c) {
      if (c.archived != _showArchived) return false;
      return q.isEmpty || c.title.toLowerCase().contains(q) || c.messages.any((m) => m.content.toLowerCase().contains(q));
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    return PageScaffold(
      title: 'AI Chat',
      subtitle: 'Conversation history + streaming OpenAI-compatible providers',
      actions: [
        OutlinedButton.icon(onPressed: _showChatsDialog, icon: const Icon(Icons.history), label: const Text('Chats')),
        const SizedBox(width: 8),
        SizedBox(
          width: 260,
          child: DropdownButtonFormField<String>(
            key: ValueKey(_providerId),
            initialValue: _providerId,
            decoration: const InputDecoration(labelText: 'Provider', isDense: true),
            items: _providers.map((p) => DropdownMenuItem(value: p.id, child: Text('${p.name} • ${p.model}', overflow: TextOverflow.ellipsis))).toList(),
            onChanged: (value) => setState(() => _providerId = value),
          ),
        ),
      ],
      child: LayoutBuilder(
        builder: (context, constraints) {
          final wide = constraints.maxWidth >= 1060;
          final chat = _ChatPane(
            providersAvailable: _providers.isNotEmpty,
            messages: _messages,
            streaming: _streaming,
            scroll: _scroll,
            controller: _controller,
            sending: _sending,
            onSend: _send,
            onStop: _stop,
          );
          if (!wide) return chat;
          return Row(
            children: [
              SizedBox(
                width: 280,
                child: _ConversationPanel(
                  conversations: _filteredConversations(),
                  currentId: _conversationId,
                  searchController: _conversationSearch,
                  showArchived: _showArchived,
                  onSearch: () => setState(() {}),
                  onToggleArchived: (v) => setState(() => _showArchived = v),
                  onNew: _newConversation,
                  onSelect: _selectConversation,
                  onRename: _rename,
                  onArchive: _toggleArchive,
                  onDelete: _deleteConversation,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(child: chat),
            ],
          );
        },
      ),
    );
  }
}

class _ChatPane extends StatelessWidget {
  const _ChatPane({
    required this.providersAvailable,
    required this.messages,
    required this.streaming,
    required this.scroll,
    required this.controller,
    required this.sending,
    required this.onSend,
    required this.onStop,
  });

  final bool providersAvailable;
  final List<ChatMessage> messages;
  final String streaming;
  final ScrollController scroll;
  final TextEditingController controller;
  final bool sending;
  final VoidCallback onSend;
  final VoidCallback onStop;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Expanded(
          child: SectionCard(
            padding: EdgeInsets.zero,
            child: !providersAvailable
                ? const Center(child: Text('ยังไม่มี Provider ที่เปิดใช้งาน • ไปที่ API Providers ก่อน'))
                : ListView.builder(
                    controller: scroll,
                    padding: const EdgeInsets.all(20),
                    itemCount: messages.length + (streaming.isNotEmpty ? 1 : 0),
                    itemBuilder: (context, index) {
                      if (index == messages.length) return _ChatBubble(role: ChatRole.assistant, content: streaming, streaming: true);
                      final message = messages[index];
                      return _ChatBubble(role: message.role, content: message.content);
                    },
                  ),
          ),
        ),
        const SizedBox(height: 12),
        SectionCard(
          padding: const EdgeInsets.fromLTRB(16, 12, 12, 12),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Expanded(child: TextField(controller: controller, minLines: 1, maxLines: 6, textInputAction: TextInputAction.newline, decoration: const InputDecoration(border: InputBorder.none, filled: false, hintText: 'ถาม Research OS…'))),
              const SizedBox(width: 10),
              if (sending)
                IconButton.filled(onPressed: onStop, tooltip: 'หยุด', icon: const Icon(Icons.stop))
              else
                IconButton.filled(onPressed: onSend, tooltip: 'ส่ง', icon: const Icon(Icons.arrow_upward)),
            ],
          ),
        ),
      ],
    );
  }
}

class _ConversationPanel extends StatelessWidget {
  const _ConversationPanel({
    required this.conversations,
    required this.currentId,
    required this.searchController,
    required this.showArchived,
    required this.onSearch,
    required this.onToggleArchived,
    required this.onNew,
    required this.onSelect,
    required this.onRename,
    required this.onArchive,
    required this.onDelete,
  });

  final List<ChatConversation> conversations;
  final String? currentId;
  final TextEditingController searchController;
  final bool showArchived;
  final VoidCallback onSearch;
  final ValueChanged<bool> onToggleArchived;
  final VoidCallback onNew;
  final ValueChanged<ChatConversation> onSelect;
  final ValueChanged<ChatConversation> onRename;
  final ValueChanged<ChatConversation> onArchive;
  final ValueChanged<ChatConversation> onDelete;

  @override
  Widget build(BuildContext context) {
    return SectionCard(
      padding: const EdgeInsets.all(10),
      child: Column(
        children: [
          Row(children: [Expanded(child: Text(showArchived ? 'Archived Chats' : 'Conversations', style: const TextStyle(fontWeight: FontWeight.w700))), IconButton.filledTonal(onPressed: onNew, tooltip: 'New Chat', icon: const Icon(Icons.add))]),
          const SizedBox(height: 8),
          TextField(controller: searchController, onChanged: (_) => onSearch(), decoration: const InputDecoration(prefixIcon: Icon(Icons.search), hintText: 'ค้นหาแชต', isDense: true)),
          const SizedBox(height: 6),
          SwitchListTile(dense: true, contentPadding: EdgeInsets.zero, value: showArchived, onChanged: onToggleArchived, title: const Text('แสดงที่เก็บถาวร')),
          const Divider(),
          Expanded(
            child: ListView.builder(
              itemCount: conversations.length,
              itemBuilder: (context, index) {
                final c = conversations[index];
                return ListTile(
                  dense: true,
                  selected: c.id == currentId,
                  title: Text(c.title, maxLines: 1, overflow: TextOverflow.ellipsis),
                  subtitle: Text('${c.messages.length} messages', style: const TextStyle(fontSize: 11)),
                  onTap: () => onSelect(c),
                  trailing: PopupMenuButton<String>(
                    onSelected: (value) {
                      if (value == 'rename') onRename(c);
                      if (value == 'archive') onArchive(c);
                      if (value == 'delete') onDelete(c);
                    },
                    itemBuilder: (_) => [
                      const PopupMenuItem(value: 'rename', child: Text('เปลี่ยนชื่อ')),
                      PopupMenuItem(value: 'archive', child: Text(c.archived ? 'นำออกจากที่เก็บถาวร' : 'เก็บถาวร')),
                      const PopupMenuItem(value: 'delete', child: Text('ลบ')),
                    ],
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _ChatBubble extends StatelessWidget {
  const _ChatBubble({required this.role, required this.content, this.streaming = false});
  final ChatRole role;
  final String content;
  final bool streaming;

  @override
  Widget build(BuildContext context) {
    final mine = role == ChatRole.user;
    final scheme = Theme.of(context).colorScheme;
    return Align(
      alignment: mine ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: const BoxConstraints(maxWidth: 820),
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 13),
        decoration: BoxDecoration(
          color: mine ? scheme.primaryContainer : const Color(0xFF171E2B),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: mine ? scheme.primary.withValues(alpha: .25) : const Color(0xFF263247)),
        ),
        child: SelectableText('$content${streaming ? ' ▍' : ''}', style: const TextStyle(height: 1.45)),
      ),
    );
  }
}

extension _FirstOrNull<T> on Iterable<T> {
  T? get firstOrNull => isEmpty ? null : first;
}
