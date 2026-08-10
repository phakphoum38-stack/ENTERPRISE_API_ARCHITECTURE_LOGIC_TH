import 'owner_api.dart';

final class OwnerStartupProbe {
  OwnerStartupProbe(this.api);

  final OwnerFriendApi api;

  Future<Map<String, dynamic>> run() async {
    final health = await api.health();
    final status = await api.status();
    return <String, dynamic>{'health': health, 'status': status};
  }
}
