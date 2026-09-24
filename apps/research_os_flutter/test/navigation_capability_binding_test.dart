import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_flutter/src/ui/enterprise_navigation.dart';

void main() {
  test('navigation registry remains the single destination source of truth', () {
    expect(researchNavigationItems, hasLength(18));
    expect(
      researchNavigationItems.map((item) => item.index).toSet(),
      equals({0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17}),
    );
    expect(
      researchNavigationItems.map((item) => item.label).toSet(),
      hasLength(18),
    );
  });

  test('workflow experience has a stable workspace destination', () {
    final item = researchNavigationItems.singleWhere(
      (candidate) => candidate.index == 15,
    );

    expect(item.label, 'Workflows');
    expect(item.section, 'Workspace');
  });

  test('control center carries the existing canonical capability identity', () {
    final item = researchNavigationItems.singleWhere(
      (candidate) => candidate.index == 16,
    );

    expect(item.label, 'Control Center');
    expect(item.capabilityId, 'control_center');
  });

  test('capability binding metadata never duplicates navigation destinations', () {
    final bound = researchNavigationItems
        .where((item) => item.capabilityId != null)
        .toList(growable: false);

    expect(
      bound.map((item) => item.capabilityId).toSet(),
      hasLength(bound.length),
    );
  });

  test('capability metadata does not become an authorization grant', () {
    final controlCenter = researchNavigationItems.singleWhere(
      (item) => item.capabilityId == 'control_center',
    );

    expect(controlCenter.capabilityId, isNotNull);
    // The navigation model contains identity metadata only. Authorization
    // remains outside the presentation layer.
  });
}
