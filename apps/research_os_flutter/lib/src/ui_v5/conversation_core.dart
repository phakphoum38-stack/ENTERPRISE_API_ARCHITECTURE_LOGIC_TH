import 'package:flutter/foundation.dart';

import '../api/research_os_api_client.dart';

/// Shared state model for the V5 Friend conversation.
///
/// The existing VoiceConversationPage remains the compatibility surface while
/// V5 workspaces migrate onto this model. Voice and text are modalities of the
/// same conversation rather than separate sessions.
@immutable
class ResearchOSConversationTurn {
  const ResearchOSConversationTurn({
    required this.id,
    required this.role,
    required this.text,
    this.memoryHits = 0,
    this.evidenceIds = const <String>[],
  });

  final String id;
  final ResearchOSConversationRole role;
  final String text;
  final int memoryHits;
  final List<String> evidenceIds;
}

enum ResearchOSConversationRole { user, friend, system }

enum ResearchOSConversationState {
  idle,
  listening,
  understanding,
  thinking,
  working,
  speaking,
  needsApproval,
  failed,
}

class ResearchOSConversationController extends ChangeNotifier {
  ResearchOSConversationController({
    required ResearchOSApiClient apiClient,
  }) : _apiClient = apiClient;

  final ResearchOSApiClient _apiClient;
  final List<ResearchOSConversationTurn> _turns = <ResearchOSConversationTurn>[];

  ResearchOSConversationState _state = ResearchOSConversationState.idle;
  bool _useMemory = true;
  String? _error;
  int _sequence = 0;

  List<ResearchOSConversationTurn> get turns => List.unmodifiable(_turns);
  ResearchOSConversationState get state => _state;
  bool get useMemory => _useMemory;
  String? get error => _error;

  set useMemory(bool value) {
    if (_useMemory == value) return;
    _useMemory = value;
    notifyListeners();
  }

  Future<ResearchOSConversationTurn?> sendText(String prompt) async {
    final normalized = prompt.trim();
    if (normalized.isEmpty ||
        _state == ResearchOSConversationState.thinking ||
        _state == ResearchOSConversationState.working ||
        _state == ResearchOSConversationState.speaking) {
      return null;
    }

    final userTurn = ResearchOSConversationTurn(
      id: _nextId('user'),
      role: ResearchOSConversationRole.user,
      text: normalized,
    );
    _turns.add(userTurn);
    _error = null;
    _state = ResearchOSConversationState.thinking;
    notifyListeners();

    try {
      final response = _useMemory
          ? await _apiClient.answerWithMemory(normalized)
          : await _apiClient.generateText(normalized);
      final answer =
          (response['text'] ?? response['answer'] ?? '').toString().trim();
      final spoken = answer.isEmpty
          ? 'ขอโทษครับ ผมไม่ได้รับคำตอบจากระบบ'
          : answer;
      final memoryHits = response['memory_hits'];
      final evidenceIds = response['evidence_ids'];
      final friendTurn = ResearchOSConversationTurn(
        id: _nextId('friend'),
        role: ResearchOSConversationRole.friend,
        text: spoken,
        memoryHits: memoryHits is List ? memoryHits.length : 0,
        evidenceIds: evidenceIds is List
            ? evidenceIds.map((item) => item.toString()).toList(growable: false)
            : const <String>[],
      );
      _turns.add(friendTurn);
      _state = ResearchOSConversationState.idle;
      notifyListeners();
      return friendTurn;
    } on Object catch (error) {
      _state = ResearchOSConversationState.failed;
      _error = error.toString();
      notifyListeners();
      return null;
    }
  }

  void setState(ResearchOSConversationState value) {
    if (_state == value) return;
    _state = value;
    notifyListeners();
  }

  void clearError() {
    _error = null;
    if (_state == ResearchOSConversationState.failed) {
      _state = ResearchOSConversationState.idle;
    }
    notifyListeners();
  }

  void clearConversation() {
    _turns.clear();
    _error = null;
    _state = ResearchOSConversationState.idle;
    notifyListeners();
  }

  String _nextId(String prefix) => '$prefix-${_sequence++}';
}
