enum ChatRole { system, user, assistant }

class ChatMessage {
  const ChatMessage({
    required this.role,
    required this.content,
    required this.createdAt,
  });

  final ChatRole role;
  final String content;
  final DateTime createdAt;

  Map<String, String> toApiJson() => {
        'role': role.name,
        'content': content,
      };
}
