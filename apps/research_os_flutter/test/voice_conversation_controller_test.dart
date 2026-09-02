import 'package:flutter_test/flutter_test.dart';

import '../lib/src/features/chat/voice_conversation_controller.dart';

void main() {
  group('VoiceConversationController', () {
    test('balanced mood keeps the configured voice', () {
      const controller = VoiceConversationController();

      expect(controller.effectiveSpeechRate, 0.48);
      expect(controller.effectivePitch, 1.05);
    });

    test('cheerful mood is slightly brighter and faster', () {
      const controller = VoiceConversationController(
        mood: FriendVoiceMood.cheerful,
      );

      expect(controller.effectiveSpeechRate, 0.53);
      expect(controller.effectivePitch, 1.09);
    });

    test('serious mood is slightly calmer and lower', () {
      const controller = VoiceConversationController(
        mood: FriendVoiceMood.serious,
      );

      expect(controller.effectiveSpeechRate, 0.44);
      expect(controller.effectivePitch, 1.01);
    });
  });
}
