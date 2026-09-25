import 'package:flutter/material.dart';
import '../../api/research_os_api_client.dart';

class AIProviderConnectionsPage extends StatefulWidget {
  const AIProviderConnectionsPage({required this.apiClient, super.key});
  final ResearchOSApiClient apiClient;
  @override State<AIProviderConnectionsPage> createState() => _AIProviderConnectionsPageState();
}

class _AIProviderConnectionsPageState extends State<AIProviderConnectionsPage> {
  Map<String,dynamic> _data=const {};
  bool _loading=true;
  String? _error;
  @override void initState(){super.initState(); _refresh();}
  Future<void> _refresh() async {
    setState(()=>_loading=true);
    try {
      final value=await widget.apiClient.getAIProviderConnections();
      if(!mounted)return;
      setState(()=>_data=value);
    } catch(e) { if(mounted)setState(()=>_error=e.toString()); }
    finally { if(mounted)setState(()=>_loading=false); }
  }
  @override Widget build(BuildContext context) {
    final providers=_data['providers'] is List ? List<dynamic>.from(_data['providers'] as List) : const <dynamic>[];
    return ListView(padding:const EdgeInsets.fromLTRB(24,24,24,40),children:[
      Row(children:[
        Container(width:46,height:46,alignment:Alignment.center,decoration:BoxDecoration(color:Theme.of(context).colorScheme.primaryContainer,borderRadius:BorderRadius.circular(14)),child:const Icon(Icons.hub_outlined)),
        const SizedBox(width:14),
        const Expanded(child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text('AI Provider Connections',style:TextStyle(fontSize:24,fontWeight:FontWeight.w700)),SizedBox(height:4),Text('GPT / OpenAI และ Gemini — Connector ก่อน API fallback')])),
        IconButton(tooltip:'รีเฟรช',onPressed:_loading?null:_refresh,icon:const Icon(Icons.refresh)),
      ]),
      const SizedBox(height:20),
      if(_loading)const LinearProgressIndicator(),
      if(_error!=null)Card(child:ListTile(leading:const Icon(Icons.error_outline),title:const Text('Connection status unavailable'),subtitle:Text(_error!))),
      ...providers.whereType<Map>().map((raw){
        final p=Map<String,dynamic>.from(raw);
        final state=p['state']?.toString()??'HOLD';
        final connected=state=='CONNECTED';
        final fallback=p['api_fallback_available']==true;
        return Card(margin:const EdgeInsets.only(bottom:12),child:Padding(padding:const EdgeInsets.all(18),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
          Row(children:[
            Icon(p['provider']=='openai'?Icons.auto_awesome_outlined:Icons.psychology_outlined,size:30),
            const SizedBox(width:12),
            Expanded(child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text(p['label']?.toString()??p['provider'].toString(),style:Theme.of(context).textTheme.titleLarge),Text('Adapter: ${p['adapter']}')])),
            Chip(label:Text(state)),
          ]),
          const SizedBox(height:12),
          Wrap(spacing:8,runSpacing:8,children:[
            FilledButton.icon(key:Key('connect-${p['provider']}'),onPressed:_loading?null:_refresh,icon:Icon(connected?Icons.check_circle_outline:Icons.link),label:Text(connected?'Connected':'Connect / Test')),
            if(fallback)const Chip(avatar:Icon(Icons.alt_route,size:16),label:Text('API fallback available')),
          ]),
          const SizedBox(height:8),
          const Text('Credentials stay on the backend. Flutter never receives provider API keys.'),
        ])));
      }),
      const SizedBox(height:12),
      const Card(child:ListTile(leading:Icon(Icons.security_outlined),title:Text('Authority boundary'),subtitle:Text('AI providers can generate, analyze and request tools; they cannot authorize, merge, release, override Owner policy, or bypass Queue / Runner / Final Gate.'))),
    ]);
  }
}
