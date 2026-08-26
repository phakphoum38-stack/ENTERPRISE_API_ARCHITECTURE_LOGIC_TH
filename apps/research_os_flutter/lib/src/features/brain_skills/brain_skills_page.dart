import 'package:flutter/material.dart';

import '../../api/research_os_api_client.dart';
import '../../ui/enterprise_components.dart';

class BrainSkillsPage extends StatefulWidget {
  const BrainSkillsPage({required this.apiClient, super.key});

  final ResearchOSApiClient apiClient;

  @override
  State<BrainSkillsPage> createState() => _BrainSkillsPageState();
}

class _BrainSkillsPageState extends State<BrainSkillsPage> {
  late Future<_BrainSnapshot> _snapshot;

  @override
  void initState() {
    super.initState();
    _snapshot = _load();
  }

  Future<_BrainSnapshot> _load() async {
    final results = await Future.wait<Map<String, dynamic>>(<Future<Map<String, dynamic>>>[
      widget.apiClient.getBrainCapacity(),
      widget.apiClient.getBrainSkills(),
      widget.apiClient.getBrainProviders(),
    ]);
    return _BrainSnapshot(
      capacity: results[0],
      skills: results[1],
      providers: results[2],
    );
  }

  void _reload() {
    setState(() => _snapshot = _load());
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: LayoutBuilder(
          builder: (context, constraints) {
            return SingleChildScrollView(
              padding: const EdgeInsets.all(20),
              child: ConstrainedBox(
                constraints: BoxConstraints(minHeight: constraints.maxHeight - 40),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    EnterprisePageHeader(
                      title: 'Brain Skills',
                      subtitle: 'ความสามารถ สมรรถนะ และ provider ของ Research OS Brain',
                      icon: Icons.psychology_outlined,
                      actions: <Widget>[
                        OutlinedButton.icon(
                          onPressed: _reload,
                          icon: const Icon(Icons.refresh),
                          label: const Text('Refresh'),
                        ),
                      ],
                    ),
                    const SizedBox(height: 20),
                    FutureBuilder<_BrainSnapshot>(
                      future: _snapshot,
                      builder: (context, snapshot) {
                        if (snapshot.connectionState != ConnectionState.done) {
                          return const Center(child: Padding(
                            padding: EdgeInsets.all(32),
                            child: CircularProgressIndicator(),
                          ));
                        }
                        if (snapshot.hasError) {
                          return Card(
                            child: Padding(
                              padding: const EdgeInsets.all(16),
                              child: Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: <Widget>[
                                  const Icon(Icons.error_outline),
                                  const SizedBox(width: 12),
                                  Expanded(
                                    child: Text('โหลด Brain Skills ไม่สำเร็จ: ${snapshot.error}'),
                                  ),
                                ],
                              ),
                            ),
                          );
                        }
                        final data = snapshot.data!;
                        return _BrainContent(snapshot: data);
                      },
                    ),
                  ],
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}

class _BrainContent extends StatelessWidget {
  const _BrainContent({required this.snapshot});

  final _BrainSnapshot snapshot;

  @override
  Widget build(BuildContext context) {
    final capacity = _displayValue(snapshot.capacity, const <String>['capacity', 'total', 'value']);
    final skillCount = _collectionCount(snapshot.skills, const <String>['skills', 'items', 'data']);
    final providerCount = _collectionCount(snapshot.providers, const <String>['providers', 'items', 'data']);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Wrap(
          spacing: 12,
          runSpacing: 12,
          children: <Widget>[
            SizedBox(
              width: 220,
              child: EnterpriseStatusTile(
                icon: Icons.memory_outlined,
                title: 'Capacity',
                value: capacity,
                caption: 'Brain capacity reported by API',
              ),
            ),
            SizedBox(
              width: 220,
              child: EnterpriseStatusTile(
                icon: Icons.auto_awesome_outlined,
                title: 'Skills',
                value: '$skillCount',
                caption: 'Skills returned by API',
              ),
            ),
            SizedBox(
              width: 220,
              child: EnterpriseStatusTile(
                icon: Icons.hub_outlined,
                title: 'Providers',
                value: '$providerCount',
                caption: 'Providers returned by API',
              ),
            ),
          ],
        ),
        const SizedBox(height: 20),
        EnterpriseSection(
          title: 'Brain contract',
          subtitle: 'Live responses from /v1/brain/capacity, /v1/brain/skills and /v1/brain/providers',
          child: Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: SelectableText(
                'Capacity: ${snapshot.capacity}\n\nSkills: ${snapshot.skills}\n\nProviders: ${snapshot.providers}',
              ),
            ),
          ),
        ),
      ],
    );
  }

  static String _displayValue(Map<String, dynamic> value, List<String> keys) {
    for (final key in keys) {
      final candidate = value[key];
      if (candidate != null && candidate.toString().trim().isNotEmpty) {
        return candidate.toString();
      }
    }
    return value.isEmpty ? '—' : value.toString();
  }

  static int _collectionCount(Map<String, dynamic> value, List<String> keys) {
    for (final key in keys) {
      final candidate = value[key];
      if (candidate is List) return candidate.length;
      if (candidate is Map) return candidate.length;
    }
    return value.isEmpty ? 0 : value.length;
  }
}

class _BrainSnapshot {
  const _BrainSnapshot({
    required this.capacity,
    required this.skills,
    required this.providers,
  });

  final Map<String, dynamic> capacity;
  final Map<String, dynamic> skills;
  final Map<String, dynamic> providers;
}
