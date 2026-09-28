import 'package:flutter_test/flutter_test.dart';

import 'package:research_os_flutter/src/features/chat/voice_conversation_controller.dart';

void main() {
  group('VoiceConversationController', () {
    test('balanced mood keeps the configured voice', () {
      final controller = VoiceConversationController();

      expect(controller.effectiveSpeechRate, 0.48);
      expect(controller.effectivePitch, 1.05);
    });

    test('cheerful mood is slightly brighter and faster', () {
      final controller = VoiceConversationController(
        mood: FriendVoiceMood.cheerful,
      );

      expect(controller.effectiveSpeechRate, 0.53);
      expect(controller.effectivePitch, 1.09);
    });

    test('serious mood is slightly calmer and lower', () {
      final controller = VoiceConversationController(
        mood: FriendVoiceMood.serious,
      );

      expect(controller.effectiveSpeechRate, 0.44);
      expect(controller.effectivePitch, 1.01);
    });
  });
}
