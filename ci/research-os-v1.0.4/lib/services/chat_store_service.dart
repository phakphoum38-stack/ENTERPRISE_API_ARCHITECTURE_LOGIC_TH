import 'dart:convert';
import 'dart:io';

import '../models/chat_conversation.dart';

class ChatStoreService {
  String get basePath {
    final base = Platform.environment['LOCALAPPDATA'] ?? r'C:\Users\Public\AppData\Local';
    return '$base\\ResearchOS\\chat\\conversations';
  }

  Future<List<ChatConversation>> listConversations() async {
    final dir = Directory(basePath);
    if (!await dir.exists()) return const [];
    final items = <ChatConversation>[];
    await for (final entity in dir.list(followLinks: false)) {
      if (entity is! File || !entity.path.toLowerCase().endsWith('.json')) continue;
      try {
        final data = jsonDecode(await entity.readAsString()) as Map<String, dynamic>;
        items.add(ChatConversation.fromJson(data));
      } catch (_) {}
    }
    items.sort((a, b) => b.updatedAt.compareTo(a.updatedAt));
    return items;
  }

  Future<ChatConversation> createConversation() async {
    final now = DateTime.now();
    final conversation = ChatConversation(
      id: '${now.microsecondsSinceEpoch}',
      title: 'New Chat',
      createdAt: now,
      updatedAt: now,
      archived: false,
      messages: const [],
    );
    await save(conversation);
    return conversation;
  }

  Future<void> save(ChatConversation conversation) async {
    final dir = Directory(basePath);
    await dir.create(recursive: true);
    final file = File('${dir.path}\\${conversation.id}.json');
    const encoder = JsonEncoder.withIndent('  ');
    await file.writeAsString(encoder.convert(conversation.toJson()), flush: true);
  }

  Future<void> delete(String id) async {
    final file = File('$basePath\\$id.json');
    if (await file.exists()) await file.delete();
  }
}
