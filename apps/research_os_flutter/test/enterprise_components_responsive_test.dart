import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_flutter/src/ui/enterprise_components.dart';

void main() {
  testWidgets('EnterprisePageHeader stacks actions below content on phones',
      (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: Center(
            child: SizedBox(
              width: 360,
              child: EnterprisePageHeader(
                title: 'AI Workspace',
                subtitle:
                    'สนทนากับ AI โดยใช้ Session History, Local Memory และ Cloud Sync ตามที่เลือก',
                icon: Icons.auto_awesome_outlined,
                actions: <Widget>[
                  OutlinedButton(
                    onPressed: null,
                    child: Text('History'),
                  ),
                  FilledButton(
                    onPressed: null,
                    child: Text('New chat'),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );

    expect(find.text('AI Workspace'), findsOneWidget);
    expect(find.text('History'), findsOneWidget);
    expect(find.text('New chat'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('EnterprisePageHeader collapses on phones while keyboard is open',
      (tester) async {
    tester.view.devicePixelRatio = 1.0;
    tester.view.physicalSize = const Size(390, 844);
    tester.view.viewInsets = const FakeViewPadding(bottom: 320);
    addTearDown(tester.view.resetDevicePixelRatio);
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetViewInsets);

    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: SizedBox(
            width: 390,
            child: EnterprisePageHeader(
              title: 'AI Workspace',
              subtitle: 'Mobile keyboard mode',
              icon: Icons.auto_awesome_outlined,
              actions: <Widget>[
                OutlinedButton(
                  onPressed: null,
                  child: Text('History'),
                ),
                FilledButton(
                  onPressed: null,
                  child: Text('New chat'),
                ),
              ],
            ),
          ),
        ),
      ),
    );

    final headerContext =
        tester.element(find.byType(EnterprisePageHeader, skipOffstage: false));
    expect(View.of(headerContext).viewInsets.bottom, 320);
    expect(find.text('AI Workspace'), findsNothing);
    expect(find.text('History'), findsNothing);
    expect(find.text('New chat'), findsNothing);
    expect(tester.takeException(), isNull);
  });
}
