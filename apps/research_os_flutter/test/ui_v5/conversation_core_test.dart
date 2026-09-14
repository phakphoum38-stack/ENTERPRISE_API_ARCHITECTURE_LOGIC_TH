import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_flutter/src/ui_v5/v5_capability.dart';

void main() {
  test('V5 user levels form a monotonic capability hierarchy', () {
    const ranks = <ResearchOSUserLevel>[
      ResearchOSUserLevel.user,
      ResearchOSUserLevel.powerUser,
      ResearchOSUserLevel.developer,
      ResearchOSUserLevel.owner,
      ResearchOSUserLevel.ownerSpecial,
    ];

    expect(ranks, hasLength(5));
    expect(ranks.indexOf(ResearchOSUserLevel.user), lessThan(ranks.indexOf(ResearchOSUserLevel.owner)));
    expect(ranks.indexOf(ResearchOSUserLevel.owner), lessThan(ranks.indexOf(ResearchOSUserLevel.ownerSpecial)));
  });
}
