/// Human-control and mutation boundary contract.
library;

enum ControlIntent {
  observe,
  analyze,
  research,
  prepare,
  propose,
  approve,
  authorize,
  execute,
  release,
  overrideHighRisk,
}

final class ControlRequest {
  const ControlRequest({
    required this.intent,
    required this.correlationId,
    this.idempotencyKey,
  });

  final ControlIntent intent;
  final String correlationId;
  final String? idempotencyKey;

  bool get requiresHumanAuthority =>
      switch (intent) {
        ControlIntent.approve ||
        ControlIntent.authorize ||
        ControlIntent.release ||
        ControlIntent.overrideHighRisk => true,
        _ => false,
      };
}
