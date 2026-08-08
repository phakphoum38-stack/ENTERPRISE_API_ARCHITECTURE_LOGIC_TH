import 'dart:io';

Future<List<String>> lanCandidates({required int port}) async {
  final prefixes = <String>{};
  final ownAddresses = <String>{};

  try {
    final interfaces = await NetworkInterface.list(
      type: InternetAddressType.IPv4,
      includeLoopback: false,
      includeLinkLocal: false,
    );

    for (final interface in interfaces) {
      for (final address in interface.addresses) {
        final ip = address.address;
        if (!_isPrivateIpv4(ip)) continue;
        ownAddresses.add(ip);
        final parts = ip.split('.');
        if (parts.length == 4) {
          prefixes.add('${parts[0]}.${parts[1]}.${parts[2]}');
        }
        if (prefixes.length >= 3) break;
      }
      if (prefixes.length >= 3) break;
    }
  } on Object {
    return const <String>[];
  }

  final result = <String>[];
  for (final prefix in prefixes) {
    for (var host = 1; host <= 254; host++) {
      final ip = '$prefix.$host';
      if (ownAddresses.contains(ip)) continue;
      result.add('http://$ip:$port');
    }
  }
  return result;
}

bool _isPrivateIpv4(String ip) {
  final parts = ip.split('.');
  if (parts.length != 4) return false;
  final values = parts.map(int.tryParse).toList(growable: false);
  if (values.any((value) => value == null)) return false;
  final a = values[0]!;
  final b = values[1]!;
  return a == 10 ||
      (a == 172 && b >= 16 && b <= 31) ||
      (a == 192 && b == 168);
}
