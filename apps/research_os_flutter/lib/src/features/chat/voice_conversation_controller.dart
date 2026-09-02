import 'package:flutter_tts/flutter_tts.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;

enum FriendVoiceMood { balanced, cheerful, serious }

class VoiceConversationController {
  VoiceConversationController({
    this.localeId = 'th-TH',
    this.speechRate = 0.48,
    this.pitch = 1.05,
    this.mood = FriendVoiceMood.balanced,
  });

  final String localeId;
  final double speechRate;
  final double pitch;
  final FriendVoiceMood mood;

  final stt.SpeechToText _speech = stt.SpeechToText();
  FlutterTts? _tts;

  bool _initialized = false;
  bool _speaking = false;
  void Function(String text, bool isFinal)? _resultCallback;

  bool get isListening => _speech.isListening;
  bool get isSpeaking => _speaking;

  double get effectiveSpeechRate => switch (mood) {
        FriendVoiceMood.balanced => speechRate,
        FriendVoiceMood.cheerful => (speechRate + .05).clamp(.1, 1.0).toDouble(),
        FriendVoiceMood.serious => (speechRate - .04).clamp(.1, 1.0).toDouble(),
      };

  double get effectivePitch => switch (mood) {
        FriendVoiceMood.balanced => pitch,
        FriendVoiceMood.cheerful => (pitch + .04).clamp(.5, 2.0).toDouble(),
        FriendVoiceMood.serious => (pitch - .04).clamp(.5, 2.0).toDouble(),
      };

  Future<bool> initialize({
    required void Function(String text, bool isFinal) onResult,
    required void Function(String message) onError,
    void Function(String status)? onStatus,
  }) async {
    if (_initialized) return true;

    final available = await _speech.initialize(
      onStatus: onStatus,
      onError: (error) => onError(error.errorMsg),
    );
    if (!available) return false;

    _tts = FlutterTts();
    _initialized = true;
    _resultCallback = onResult;

    final tts = _tts!;
    await tts.setLanguage(localeId);
    await tts.setSpeechRate(effectiveSpeechRate);
    await tts.setPitch(effectivePitch);
    await tts.setVolume(1.0);
    tts.setStartHandler(() => _speaking = true);
    tts.setCompletionHandler(() => _speaking = false);
    tts.setCancelHandler(() => _speaking = false);
    tts.setErrorHandler((_) => _speaking = false);
    return true;
  }

  Future<bool> startListening({String? locale}) async {
    if (!_initialized) return false;
    final tts = _tts;
    if (tts != null) await tts.stop();
    _speaking = false;
    await _speech.listen(
      listenOptions: stt.SpeechListenOptions(
        localeId: locale ?? localeId,
        listenFor: const Duration(seconds: 45),
        pauseFor: const Duration(seconds: 3),
        partialResults: true,
        cancelOnError: false,
        listenMode: stt.ListenMode.dictation,
      ),
      onResult: (result) => _resultCallback?.call(
        result.recognizedWords,
        result.finalResult,
      ),
    );
    return _speech.isListening;
  }

  Future<void> stopListening() async {
    if (_speech.isListening) {
      await _speech.stop();
    }
  }

  Future<void> cancelListening() async {
    if (_speech.isListening) {
      await _speech.cancel();
    }
  }

  Future<void> speak(String text) async {
    final normalized = _prepareForSpeech(text);
    if (normalized.isEmpty) return;
    await _speech.stop();
    final tts = _tts;
    if (tts == null) return;
    await tts.stop();
    await tts.setSpeechRate(effectiveSpeechRate);
    await tts.setPitch(effectivePitch);
    _speaking = true;
    await tts.speak(normalized);
  }

  Future<void> stopSpeaking() async {
    final tts = _tts;
    if (tts != null) await tts.stop();
    _speaking = false;
  }

  Future<void> dispose() async {
    await _speech.cancel();
    final tts = _tts;
    if (tts != null) await tts.stop();
    _speaking = false;
  }

  String _prepareForSpeech(String text) {
    return text
        .replaceAll(RegExp(r'```[\s\S]*?```'), ' ')
        .replaceAll(RegExp(r'`([^`]*)`'), r'$1')
        .replaceAll(RegExp(r'\*\*([^*]+)\*\*'), r'$1')
        .replaceAll(RegExp(r'\*([^*]+)\*'), r'$1')
        .replaceAll(RegExp(r'#{1,6}\s*'), '')
        .replaceAll(RegExp(r'\[([^\]]+)\]\([^\)]+\)'), r'$1')
        .replaceAll(RegExp(r'\n{3,}'), '\n\n')
        .trim();
  }
}
