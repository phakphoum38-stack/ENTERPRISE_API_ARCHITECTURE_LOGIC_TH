import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:research_os_flutter/src/api/developer_access_api_client.dart';
import 'package:research_os_flutter/src/features/developer_access/flutter_code_tool_page.dart';

void main() {
  testWidgets('Flutter Code Tool completes select, read, preview and apply lifecycle', (tester) async {
    var applied = false;
    final client = MockClient((request) async {
      if (request.url.path == '/v2/developer/code/projects') {
        return http.Response(jsonEncode({
          'api_version': 'v2',
          'projects': {'research_os_flutter': 'apps/research_os_flutter'},
        }), 200);
      }
      if (request.url.path == '/v2/developer/code/files') {
        return http.Response(jsonEncode({
          'api_version': 'v2',
          'items': [{'path': 'lib/main.dart', 'bytes': 20}],
        }), 200);
      }
      if (request.url.pathSegments.length == 5 &&
          request.url.pathSegments[0] == 'v2' &&
          request.url.pathSegments[1] == 'developer' &&
          request.url.pathSegments[2] == 'code' &&
          request.url.pathSegments[3] == 'file' &&
          request.url.pathSegments[4] == 'lib/main.dart') {
        return http.Response(jsonEncode({
          'api_version': 'v2',
          'project': 'research_os_flutter',
          'path': 'lib/main.dart',
          'content': 'void main() {}\\n',
          'sha256': 'old-sha',
        }), 200);
      }
      if (request.url.path == '/v2/developer/code/preview') {
        return http.Response(jsonEncode({
          'api_version': 'v2',
          'changed': true,
          'diff': '--- a/lib/main.dart\\n+++ b/lib/main.dart\\n+print(1);\\n',
        }), 200);
      }
      if (request.url.path == '/v2/developer/code/apply') {
        applied = true;
        return http.Response(jsonEncode({
          'api_version': 'v2',
          'applied': true,
          'rolled_back': false,
          'sha256': 'new-sha',
          'validation': {'ok': true, 'steps': []},
        }), 200);
      }
      return http.Response('{}', 404);
    });

    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: FlutterCodeToolPage(
          client: DeveloperAccessApiClient(
            baseUrl: 'https://developer.example.test',
            client: client,
          ),
          principal: 'owner@example.com',
        ),
      ),
    ));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('flutter-code-tool')), findsOneWidget);
    expect(find.text('research_os_flutter'), findsOneWidget);

    await tester.tap(find.byKey(const Key('flutter-code-tool-file')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('lib/main.dart').last);
    await tester.pumpAndSettle();
    await tester.pump(const Duration(milliseconds: 50));

    final readButton = find.byKey(const Key('flutter-code-tool-read'));
    expect(readButton, findsOneWidget);
    await tester.ensureVisible(readButton);
    await tester.tap(readButton);
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('flutter-code-tool-status')), findsOneWidget);
    final readSha = find.byKey(const Key('flutter-code-tool-read-sha'));
    expect(readSha, findsOneWidget);
    await tester.scrollUntilVisible(
      readSha,
      300,
      scrollable: find.descendant(
        of: find.byKey(const Key('flutter-code-tool-scroll')),
        matching: find.byType(Scrollable),
      ).first,
    );
    expect(readSha, findsOneWidget);
    await tester.enterText(find.byType(TextField).last, 'void main() { print(1); }\\n');

    final previewButton = find.widgetWithText(FilledButton, 'Preview Diff');
    expect(previewButton, findsOneWidget);
    await tester.ensureVisible(previewButton);
    await tester.tap(previewButton);
    await tester.pumpAndSettle();

    expect(find.textContaining('Preview Diff'), findsWidgets);

    final applyButton = find.widgetWithText(FilledButton, 'Apply Change');
    expect(applyButton, findsOneWidget);
    await tester.ensureVisible(applyButton);
    await tester.tap(applyButton);
    await tester.pumpAndSettle();
    expect(applied, isTrue);
  });
}
