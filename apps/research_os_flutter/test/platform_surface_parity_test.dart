import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_flutter/src/ui/enterprise_navigation.dart';
import 'package:research_os_flutter/src/ui/research_os_sidebar_v2.dart';

import 'helpers/research_os_test_navigation.dart';

void main() {
  testWidgets(
    'mobile Research OS navigation exposes the complete shared application surface',
    (tester) async {
      final scaffoldKey = GlobalKey<ScaffoldState>();
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            key: scaffoldKey,
            drawer: ResearchMobileDrawer(
              selectedIndex: 0,
              onSelected: (_) {},
            ),
            body: const SizedBox.shrink(),
          ),
        ),
      );

      await ResearchOsTestNavigation.openMobileDrawer(tester, scaffoldKey);

      expect(find.byType(ResearchMobileDrawer), findsOneWidget);

      await ResearchOsTestNavigation.assertAllDestinations(
        tester,
        surface: ResearchNavigationSurface.mobile,
        scrollable: find.descendant(
          of: find.byType(ResearchMobileDrawer),
          matching: find.byType(Scrollable),
        ).first,
      );
    },
  );

  testWidgets(
    'desktop Research OS navigation uses the same shared application surface',
    (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ResearchOSSidebarV2(
              expanded: true,
              selectedIndex: 0,
              onToggle: () {},
              onSelected: (_) {},
            ),
          ),
        ),
      );

      await ResearchOsTestNavigation.openDesktopNavigation(tester);

      await ResearchOsTestNavigation.assertAllDestinations(
        tester,
        surface: ResearchNavigationSurface.desktop,
        scrollable: find.descendant(
          of: find.byKey(const Key('desktop-navigation-list-v2')),
          matching: find.byType(Scrollable),
        ).first,
      );
    },
  );
}
