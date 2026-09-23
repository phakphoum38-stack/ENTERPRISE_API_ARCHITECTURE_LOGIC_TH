import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_flutter/src/ui/enterprise_navigation.dart';
import 'package:research_os_flutter/src/ui/research_os_sidebar_v2.dart';

void main() {
  testWidgets(
    'mobile Research OS navigation exposes the complete shared application surface',
    (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ResearchMobileDrawer(
              selectedIndex: 0,
              onSelected: (_) {},
            ),
          ),
        ),
      );

      expect(find.byType(ResearchMobileDrawer), findsOneWidget);

      for (final item in researchNavigationItems) {
        final finder = find.byKey(
          Key('mobile-nav-${item.index}'),
          skipOffstage: false,
        );
        await tester.scrollUntilVisible(
          finder,
          300,
          scrollable: find.descendant(
            of: find.byType(ResearchMobileDrawer),
            matching: find.byType(Scrollable),
          ),
        );
        expect(
          finder,
          findsOneWidget,
          reason: 'Missing mobile navigation destination: ${item.label}',
        );
        expect(find.text(item.label), findsOneWidget);
      }
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

      expect(find.byType(ResearchOSSidebarV2), findsOneWidget);

      for (final item in researchNavigationItems) {
        final finder = find.byKey(
          Key('v2-nav-${item.index}'),
          skipOffstage: false,
        );
        await tester.scrollUntilVisible(
          finder,
          300,
          scrollable: find.descendant(
            of: find.byKey(const Key('desktop-navigation-list-v2')),
            matching: find.byType(Scrollable),
          ),
        );
        expect(
          finder,
          findsOneWidget,
          reason: 'Missing desktop navigation destination: ${item.label}',
        );
        expect(
          find.text(item.label, skipOffstage: false),
          findsOneWidget,
        );
      }
    },
  );

  test(
    'shared navigation registry contains one stable destination for every app page',
    () {
      expect(researchNavigationItems.length, 15);

      final indexes = researchNavigationItems.map((item) => item.index).toSet();
      expect(indexes, equals({0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14}));

      final labels = researchNavigationItems.map((item) => item.label).toSet();
      expect(labels.length, researchNavigationItems.length);
    },
  );
}
