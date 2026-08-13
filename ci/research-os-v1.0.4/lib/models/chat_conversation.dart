import 'chat_message.dart';

class ChatConversation {
  const ChatConversation({
    required this.id,
    required this.title,
    required this.createdAt,
    required this.updatedAt,
    required this.archived,
    required this.messages,
  });

  final String id;
  final String title;
  final DateTime createdAt;
  final DateTime updatedAt;
  final bool archived;
  final List<ChatMessage> messages;

  ChatConversation copyWith({
    String? title,
    DateTime? updatedAt,
    bool? archived,
    List<ChatMessage>? messages,
  }) {
    return ChatConversation(
      id: id,
      title: title ?? this.title,
      createdAt: createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      archived: archived ?? this.archived,
      messages: messages ?? this.messages,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'title': title,
        'createdAt': createdAt.toIso8601String(),
        'updatedAt': updatedAt.toIso8601String(),
        'archived': archived,
        'messages': messages
            .map((m) => {
                  'role': m.role.name,
                  'content': m.content,
                  'createdAt': m.createdAt.toIso8601String(),
                })
            .toList(),
      };

  factory ChatConversation.fromJson(Map<String, dynamic> json) {
    final messages = <ChatMessage>[];
    for (final raw in (json['messages'] as List<dynamic>? ?? const [])) {
      final m = Map<String, dynamic>.from(raw as Map);
      final roleName = '${m['role'] ?? 'user'}';
      final role = ChatRole.values.where((r) => r.name == roleName).firstOrNull ?? ChatRole.user;
      messages.add(ChatMessage(
        role: role,
        content: '${m['content'] ?? ''}',
        createdAt: DateTime.tryParse('${m['createdAt'] ?? ''}') ?? DateTime.now(),
      ));
    }
    return ChatConversation(
      id: '${json['id'] ?? ''}',
      title: '${json['title'] ?? 'New Chat'}',
      createdAt: DateTime.tryParse('${json['createdAt'] ?? ''}') ?? DateTime.now(),
      updatedAt: DateTime.tryParse('${json['updatedAt'] ?? ''}') ?? DateTime.now(),
      archived: json['archived'] == true,
      messages: messages,
    );
  }
}

extension _FirstOrNull<T> on Iterable<T> {
  T? get firstOrNull => isEmpty ? null : first;
}
