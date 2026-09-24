import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:research_os_flutter/src/ui/enterprise_navigation.dart';

/// Shared widget-test helpers for the Research OS application surface.
///
/// Tests should use the same navigation registry as production instead of
/// maintaining platform-specific destination lists or finder logic.
class ResearchOsTestNavigation {
  const ResearchOsTestNavigation._();

  static Finder findDestination(
    int index, {
    required ResearchNavigationSurface surface,
    bool skipOffstage = false,
  }) {
    return find.byKey(
      Key('${surface.destinationKeyPrefix}$index'),
      skipOffstage: skipOffstage,
    );
  }

  static Finder findLabel(
    int index, {
    required ResearchNavigationSurface surface,
    bool skipOffstage = false,
  }) {
    return find.byKey(
      Key('${surface.labelKeyPrefix}$index'),
      skipOffstage: skipOffstage,
    );
  }

  static Future<void> openMobileDrawer(
    WidgetTester tester,
    GlobalKey<ScaffoldState> scaffoldKey,
  ) async {
    final scaffold = scaffoldKey.currentState;
    if (scaffold == null) {
      throw StateError('Mobile navigation ScaffoldState is not mounted.');
    }
    scaffold.openDrawer();
    await tester.pumpAndSettle();
  }

  static Future<void> openDesktopNavigation(
    WidgetTester tester, {
    Finder? sidebar,
  }) async {
    final target = sidebar ?? find.byKey(
      const Key('research-os-sidebar-v2'),
    );
    expect(target, findsOneWidget);

    final expandedLabel = find.byKey(
      const Key('desktop-nav-label-0'),
      skipOffstage: false,
    );
    if (expandedLabel.evaluate().isNotEmpty) {
      return;
    }

    final toggle = find.byKey(
      const Key('toggle-desktop-sidebar-v2'),
      skipOffstage: false,
    );
    expect(toggle, findsOneWidget);
    await tester.tap(toggle);
    await tester.pumpAndSettle();
  }

  static Future<void> ensureVisible(
    WidgetTester tester, {
    required Finder target,
    required Finder scrollable,
    double delta = 300,
  }) async {
    await tester.scrollUntilVisible(
      target,
      delta,
      scrollable: scrollable,
    );
  }

  static Future<void> assertAllDestinations(
    WidgetTester tester, {
    required ResearchNavigationSurface surface,
    required Finder scrollable,
  }) async {
    expect(
      researchNavigationItems.length,
      15,
      reason: 'The shared application surface must contain 15 destinations.',
    );

    final indexes = researchNavigationItems.map((item) => item.index).toSet();
    expect(
      indexes,
      equals({0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14}),
      reason: 'Navigation indexes must remain stable and complete.',
    );

    final labels = researchNavigationItems.map((item) => item.label).toSet();
    expect(
      labels.length,
      researchNavigationItems.length,
      reason: 'Navigation labels must remain unique.',
    );

    for (final item in researchNavigationItems) {
      final destination = findDestination(
        item.index,
        surface: surface,
        skipOffstage: false,
      );
      await ensureVisible(
        tester,
        target: destination,
        scrollable: scrollable,
      );
      expect(
        destination,
        findsOneWidget,
        reason: 'Missing ${surface.name} destination: ${item.label}',
      );
      expect(
        findLabel(
          item.index,
          surface: surface,
          skipOffstage: false,
        ),
        findsOneWidget,
        reason: 'Missing ${surface.name} label: ${item.label}',
      );
    }
  }
}

enum ResearchNavigationSurface {
  mobile('mobile', 'mobile-nav-', 'mobile-nav-label-'),
  desktop('desktop', 'v2-nav-', 'desktop-nav-label-');

  const ResearchNavigationSurface(
    this.name,
    this.destinationKeyPrefix,
    this.labelKeyPrefix,
  );

  final String name;
  final String destinationKeyPrefix;
  final String labelKeyPrefix;
}
