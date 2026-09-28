/// Shared separation of presentation, domain and trust state.
library;

enum ViewLifecycleState {
  discovered,
  loaded,
  active,
  transitioning,
  suspended,
  recovering,
  closed,
}

enum TrustState {
  unassessed,
  observed,
  supported,
  verified,
  contradicted,
  hold,
}

abstract interface class StateContract {
  ViewLifecycleState get viewState;
  TrustState get trustState;
  Map<String, Object?> snapshot();
  Future<void> recover();
}
