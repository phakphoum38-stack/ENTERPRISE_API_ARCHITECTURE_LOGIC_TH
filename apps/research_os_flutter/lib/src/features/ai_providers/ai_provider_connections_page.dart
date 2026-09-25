import 'package:flutter/material.dart';
import '../../api/research_os_api_client.dart';

class AIProviderConnectionsPage extends StatefulWidget {
  const AIProviderConnectionsPage({required this.apiClient, super.key});
  final ResearchOSApiClient apiClient;
  @override State<AIProviderConnectionsPage> createState()=>_AIProviderConnectionsPageState();
}

class _AIProviderConnectionsPageState extends State<AIProviderConnectionsPage> {
  Map<String,dynamic>? _payload;
  String? _error;
  String? _busyProvider;
  @override void initState(){super.initState();_load();}
  Future<void> _load() async {
    try { final payload=await widget.apiClient.getAIProviderConnections(); if(!mounted)return; setState((){_payload=payload;_error=null;}); }
    catch(error){if(!mounted)return;setState(()=>_error=error.toString());}
  }
  Future<void> _connect(String provider) async {
    setState(()=>_busyProvider=provider);
    try { final payload=await widget.apiClient.connectAIProvider(provider); if(!mounted)return; setState((){_payload=payload;_error=null;}); }
    catch(error){if(!mounted)return;setState(()=>_error=error.toString());}
    finally{if(mounted)setState(()=>_busyProvider=null);}
  }
  Future<void> _disconnect(String provider) async {
    setState(()=>_busyProvider=provider);
    try { final payload=await widget.apiClient.disconnectAIProvider(provider); if(!mounted)return; setState((){_payload=payload;_error=null;}); }
    catch(error){if(!mounted)return;setState(()=>_error=error.toString());}
    finally{if(mounted)setState(()=>_busyProvider=null);}
  }
  List<Map<String,dynamic>> get _providers {
    final values=_payload?['providers'];
    if(values is! List)return const <Map<String,dynamic>>[];
    return values.whereType<Map>().map((value)=>Map<String,dynamic>.from(value)).toList();
  }
  @override Widget build(BuildContext context) {
    final scheme=Theme.of(context).colorScheme;
    return Scaffold(
      appBar:AppBar(title:const Text('AI Providers')),
      body:RefreshIndicator(
        onRefresh:_load,
        child:ListView(
          padding:const EdgeInsets.all(20),
          children:<Widget>[
            Card(child:Padding(padding:const EdgeInsets.all(18),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:<Widget>[
              Text('Connection Registry',style:Theme.of(context).textTheme.titleLarge),
              const SizedBox(height:8),
              const Text('Connector first. API fallback second. Credentials stay on the Research OS server.'),
              const SizedBox(height:14),
              Wrap(spacing:8,runSpacing:8,children:<Widget>[
                Chip(avatar:Icon(Icons.security_outlined,size:17,color:scheme.primary),label:const Text('Server-side credentials')),
                Chip(avatar:Icon(Icons.rule_outlined,size:17,color:scheme.primary),label:const Text('Final Gate authority')),
              ]),
            ]))),
            if(_error!=null)...<Widget>[
              const SizedBox(height:12),
              Card(child:ListTile(leading:const Icon(Icons.error_outline),title:const Text('Connection registry unavailable'),subtitle:Text(_error!))),
            ],
            const SizedBox(height:12),
            for(final provider in _providers)
              _ProviderCard(
                provider:provider,
                busy:_busyProvider==provider['id'],
                onConnect:()=>_connect(provider['id'] as String),
                onDisconnect:()=>_disconnect(provider['id'] as String),
              ),
            if(_providers.isEmpty&&_error==null)
              const Padding(padding:EdgeInsets.all(32),child:Center(child:CircularProgressIndicator())),
          ],
        ),
      ),
    );
  }
}

class _ProviderCard extends StatelessWidget {
  const _ProviderCard({required this.provider,required this.busy,required this.onConnect,required this.onDisconnect});
  final Map<String,dynamic> provider;
  final bool busy;
  final VoidCallback onConnect;
  final VoidCallback onDisconnect;
  @override Widget build(BuildContext context) {
    final state=(provider['state']??'HOLD').toString();
    final route=provider['route'];
    final connected=state=='CONNECTED'||state=='API_FALLBACK';
    final label=(provider['label']??provider['id']).toString();
    final model=(provider['model']??'server default').toString();
    final routeText=(route??'PLATFORM_API_FALLBACK').toString();
    final summary=connected ? 'Route: $routeText • Model: $model' : 'Route: PLATFORM_API_FALLBACK • Credentials are not exposed to the client.';
    return Card(
      margin:const EdgeInsets.only(bottom:12),
      child:Padding(padding:const EdgeInsets.all(18),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:<Widget>[
        Row(children:<Widget>[
          CircleAvatar(child:Icon(provider['id']=='openai'?Icons.auto_awesome_outlined:Icons.auto_awesome_mosaic_outlined)),
          const SizedBox(width:12),
          Expanded(child:Text(label,style:Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight:FontWeight.w700))),
          Chip(label:Text(state)),
        ]),
        const SizedBox(height:10),
        Text(summary),
        const SizedBox(height:14),
        Row(children:<Widget>[
          FilledButton.icon(
            onPressed:busy?null:onConnect,
            icon:busy?const SizedBox(width:16,height:16,child:CircularProgressIndicator(strokeWidth:2)):const Icon(Icons.link),
            label:Text(connected?'Reconnect / Health Check':'Connect'),
          ),
          const SizedBox(width:8),
          OutlinedButton(onPressed:busy||!connected?null:onDisconnect,child:const Text('Disconnect')),
        ]),
      ])),
    );
  }
}
