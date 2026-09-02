import 'package:flutter_tts/flutter_tts.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;

class VoiceConversationController {
  VoiceConversationController({
    this.localeId = 'th-TH',
    this.speechRate = 0.48,
    this.pitch = 1.05,
  });

  final String localeId;
  final double speechRate;
  final double pitch;

  final stt.SpeechToText _speech = stt.SpeechToText();
  final FlutterTts _tts = FlutterTts();

  bool _initialized = false;
  bool _speaking = false;

  bool get isListening => _speech.isListening;
  bool get isSpeaking => _speaking;

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

    _speech.statusListener = onStatus;
    _speech.errorListener = (error) => onError(error.errorMsg);
    _speech.listenFor = const Duration(seconds: 45);
    _speech.pauseFor = const Duration(seconds: 3);

    // Re-initialize with the result callback so platform-specific callbacks
    // stay owned by this controller.
    await _speech.initialize(
      onStatus: onStatus,
      onError: (error) => onError(error.errorMsg),
    );

    _initialized = true;
    await _tts.setLanguage(localeId);
    await _tts.setSpeechRate(speechRate);
    await _tts.setPitch(pitch);
    await _tts.setVolume(1.0);
    _tts.setStartHandler(() => _speaking = true);
    _tts.setCompletionHandler(() => _speaking = false);
    _tts.setCancelHandler(() => _speaking = false);
    _tts.setErrorHandler((_) => _speaking = false);

    _resultCallback = onResult;
    return true;
  }

  void Function(String text, bool isFinal)? _resultCallback;

  Future<bool> startListening({String? locale}) async {
    if (!_initialized) return false;
    await _tts.stop();
    _speaking = false;
    await _speech.listen(
      localeId: locale ?? localeId,
      listenOptions: stt.SpeechListenOptions(
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
    final normalized = text.trim();
    if (normalized.isEmpty) return;
    await _speech.stop();
    await _tts.stop();
    _speaking = true;
    await _tts.speak(normalized);
  }

  Future<void> stopSpeaking() async {
    await _tts.stop();
    _speaking = false;
  }

  Future<void> dispose() async {
    await _speech.cancel();
    await _tts.stop();
    _speaking = false;
  }
}
