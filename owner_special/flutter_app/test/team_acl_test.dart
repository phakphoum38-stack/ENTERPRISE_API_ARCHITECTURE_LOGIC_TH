import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';

void main() {
  late Map<String, dynamic> contract;

  setUp(() {
    contract = jsonDecode('''
{
  "roles": {
    "owner": {"switch_team": true, "create_team": true, "admin": true},
    "member": {"switch_team": true, "create_team": false, "admin": false},
    "viewer": {"switch_team": false, "create_team": false, "admin": false}
  },
  "services": {
    "8787": "workspace",
    "8788": "team",
    "8790": "friend-internal"
  }
}
''') as Map<String, dynamic>;
  });

  test('owner has full team controls', () {
    final owner = Map<String, dynamic>.from(contract['roles']['owner'] as Map);
    expect(owner['switch_team'], isTrue);
    expect(owner['create_team'], isTrue);
    expect(owner['admin'], isTrue);
  });

  test('member cannot create teams or administer', () {
    final member = Map<String, dynamic>.from(contract['roles']['member'] as Map);
    expect(member['switch_team'], isTrue);
    expect(member['create_team'], isFalse);
    expect(member['admin'], isFalse);
  });

  test('viewer has no team mutation access', () {
    final viewer = Map<String, dynamic>.from(contract['roles']['viewer'] as Map);
    expect(viewer['switch_team'], isFalse);
    expect(viewer['create_team'], isFalse);
    expect(viewer['admin'], isFalse);
  });

  test('owner service topology contains only implemented contracts', () {
    final services = Map<String, dynamic>.from(contract['services'] as Map);
    expect(services.keys.toSet(), {'8787', '8788', '8790'});
    expect(services['8787'], 'workspace');
    expect(services['8788'], 'team');
    expect(services['8790'], 'friend-internal');
    expect(services.containsKey('8789'), isFalse);
  });
}
