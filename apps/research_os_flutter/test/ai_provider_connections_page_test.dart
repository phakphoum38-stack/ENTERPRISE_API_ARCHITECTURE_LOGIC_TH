import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_flutter/src/api/research_os_api_client.dart';
import 'package:research_os_flutter/src/features/ai_providers/ai_provider_connections_page.dart';

class _FakeApiClient extends ResearchOSApiClient {
  _FakeApiClient():super(baseUrl:'http://example.test');
  @override Future<Map<String,dynamic>> getAIProviderConnections() async => <String,dynamic>{
    'providers':<Map<String,dynamic>>[
      <String,dynamic>{'id':'openai','label':'OpenAI / GPT','state':'UNAVAILABLE','route':'PLATFORM_API_FALLBACK','model':'gpt-5.6'},
      <String,dynamic>{'id':'gemini','label':'Google Gemini','state':'UNAVAILABLE','route':'PLATFORM_API_FALLBACK','model':'gemini-2.5-flash'},
    ],
  };
  @override Future<Map<String,dynamic>> connectAIProvider(String provider) async => <String,dynamic>{
    'providers':<Map<String,dynamic>>[
      <String,dynamic>{'id':provider,'label':provider=='openai'?'OpenAI / GPT':'Google Gemini','state':'API_FALLBACK','route':'PLATFORM_API_FALLBACK','model':'test-model'},
    ],
  };
  @override Future<Map<String,dynamic>> disconnectAIProvider(String provider) async => <String,dynamic>{
    'providers':<Map<String,dynamic>>[
      <String,dynamic>{'id':provider,'label':provider=='openai'?'OpenAI / GPT':'Google Gemini','state':'NOT_CONNECTED','route':null,'model':'test-model'},
    ],
  };
}
void main(){
  testWidgets('AI provider page renders GPT and Gemini connect controls',(tester)async{
    await tester.pumpWidget(MaterialApp(home:AIProviderConnectionsPage(apiClient:_FakeApiClient())));
    await tester.pumpAndSettle();
    expect(find.text('OpenAI / GPT'),findsOneWidget);
    expect(find.text('Google Gemini'),findsOneWidget);
    expect(find.text('Connect'),findsNWidgets(2));
    expect(find.text('Server-side credentials'),findsOneWidget);
  });
  testWidgets('AI provider page connects through the API boundary',(tester)async{
    await tester.pumpWidget(MaterialApp(home:AIProviderConnectionsPage(apiClient:_FakeApiClient())));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Connect').first);
    await tester.pumpAndSettle();
    expect(find.text('API_FALLBACK'),findsOneWidget);
  });
}
