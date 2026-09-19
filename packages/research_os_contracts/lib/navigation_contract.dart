/// Shared declarative navigation contract.
///
/// Features describe destinations; the canonical shell owns global navigation.
library;

final class NavigationDestinationContract {
  const NavigationDestinationContract({
    required this.id,
    required this.label,
    required this.route,
    this.capability,
    this.requiredAuthority,
  });

  final String id;
  final String label;
  final String route;
  final String? capability;
  final String? requiredAuthority;
}

abstract interface class NavigationContract {
  List<NavigationDestinationContract> destinations();
  String get activeDestination;
  Future<void> navigate(String destinationId);
}
