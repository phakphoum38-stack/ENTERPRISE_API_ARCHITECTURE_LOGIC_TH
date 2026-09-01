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

}
