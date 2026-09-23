import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_flutter/src/ui/enterprise_navigation.dart';

void main() {
  testWidgets(
    'mobile Research OS navigation exposes the complete shared application surface',
    (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            drawer: ResearchMobileDrawer(
              selectedIndex: 0,
              onSelected: (_) {},
            ),
          ),
        ),
      );

      final drawer = find.byType(ResearchMobileDrawer);
      expect(drawer, findsOneWidget);

      for (final item in researchNavigationItems) {
        expect(
          find.byKey(Key('mobile-nav-${item.index}')),
          findsOneWidget,
          reason: 'Missing mobile navigation destination: ${item.label}',
        );
        expect(find.text(item.label), findsOneWidget);
      }

      expect(researchNavigationItems.length, 15);
    },
  );
}
