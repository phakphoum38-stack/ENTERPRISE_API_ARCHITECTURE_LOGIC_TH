import 'package:flutter/material.dart';

import '../../api/research_os_api_client.dart';

class BrainSkillsPage extends StatefulWidget {
  const BrainSkillsPage({required this.apiClient, super.key});

  final ResearchOSApiClient apiClient;

  @override
  State<BrainSkillsPage> createState() => _BrainSkillsPageState();
}

class _BrainSkillsPageState extends State<BrainSkillsPage> {
  bool _loading = true;
  String? _error;
  Map<String, dynamic> _capacity = const <String, dynamic>{};
  Map<String, dynamic> _brain = const <String, dynamic>{};
  Map<String, dynamic> _providers = const <String, dynamic>{};

  @override
  void initState() {
    super.initState();
    _refresh();
  }

  static Map<String, dynamic> _map(Object? value) =>
      value is Map ? Map<String, dynamic>.from(value) : <String, dynamic>{};

  static List<Map<String, dynamic>> _maps(Object? value) => value is List
      ? value.whereType<Map>().map(_map).toList()
      : <Map<String, dynamic>>[];

  Future<void> _refresh() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final results = await Future.wait<Map<String, dynamic>>(
        <Future<Map<String, dynamic>>>[
          widget.apiClient.getBrainCapacity(),
          widget.apiClient.getBrainSkills(),
          widget.apiClient.getBrainProviders(),
        ],
      );
      if (!mounted) return;
      setState(() {
        _capacity = _map(results[0]['capacity']);
        _brain = _map(results[1]['brain']);
        _providers = _map(results[2]['providers']);
        _loading = false;
      });
    } on Object catch (error) {
      if (!mounted) return;
      setState(() {
        _error = error.toString();
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final skills = _maps(_brain['skills']);
    final modes = _maps(_capacity['assistant_modes']);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Brain Skills'),
        actions: <Widget>[
          IconButton(
            key: const Key('refresh-brain-skills'),
            tooltip: 'Refresh Brain Skills',
            onPressed: _loading ? null : _refresh,
            icon: const Icon(Icons.refresh),
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: ListView(
          key: const Key('brain-skills-page'),
          padding: const EdgeInsets.fromLTRB(24, 18, 24, 32),
          children: <Widget>[
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: <Color>[
                    scheme.primaryContainer,
                    scheme.tertiaryContainer,
                  ],
                ),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Row(
                children: <Widget>[
                  Icon(Icons.psychology_alt_outlined,
                      size: 52, color: scheme.primary),
                  const SizedBox(width: 18),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Text(
                          'Adaptive Brain 6³ → 6⁶',
                          key: const Key('brain-skills-heading'),
                          style: Theme.of(context)
                              .textTheme
                              .headlineSmall
                              ?.copyWith(fontWeight: FontWeight.w800),
                        ),
                        const SizedBox(height: 5),
                        const Text(
                          'ผู้ช่วยแบบยืดหยุ่น ใช้กำลังตามงาน งบ และความพร้อมของระบบ',
                        ),
                      ],
                    ),
                  ),
                  _StateBadge(
                    label: _loading ? 'Loading' : _error == null ? 'Ready' : 'Offline',
                    ready: !_loading && _error == null,
                  ),
                ],
              ),
            ),
            if (_loading) ...<Widget>[
              const SizedBox(height: 14),
              const LinearProgressIndicator(),
            ],
            if (_error != null) ...<Widget>[
              const SizedBox(height: 16),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(18),
                  child: Row(
                    children: <Widget>[
                      Icon(Icons.error_outline, color: scheme.error),
                      const SizedBox(width: 12),
                      Expanded(child: Text(_error!)),
                      TextButton(onPressed: _refresh, child: const Text('Retry')),
                    ],
                  ),
                ),
              ),
            ],
            const SizedBox(height: 24),
            const _SectionTitle(
              title: 'Assistant modes',
              subtitle: '6³ เป็นโหมดใช้งานทั่วไป และ 6⁶ เป็นเพดานสำหรับงานซับซ้อน',
            ),
            const SizedBox(height: 12),
            LayoutBuilder(
              builder: (context, constraints) {
                final columns = constraints.maxWidth >= 760 ? 2 : 1;
                final width =
                    (constraints.maxWidth - ((columns - 1) * 12)) / columns;
                final visibleModes = modes.isEmpty
                    ? <Map<String, dynamic>>[
                        <String, dynamic>{
                          'mode': 'assistant_6x3',
                          'label': 'Adaptive 6^3 Assistant Crew',
                          'theoretical_assistants':
                              _capacity['assistant_6x3_capacity'] ?? 216,
                          'recommended_max_active_workers':
                              _capacity['max_active_workers'] ?? 36,
                        },
                        <String, dynamic>{
                          'mode': 'compound_6x6',
                          'label': 'Adaptive 6^6 Compound Brain',
                          'theoretical_assistants':
                              _capacity['max_leaf_capacity'] ?? 46656,
                          'recommended_max_active_workers':
                              _capacity['hard_active_worker_limit'] ?? 1296,
                        },
                      ]
                    : modes;
                return Wrap(
                  spacing: 12,
                  runSpacing: 12,
                  children: visibleModes
                      .map(
                        (mode) => SizedBox(
                          width: width,
                          child: _ModeCard(
                            mode: mode,
                            selected: mode['mode'] ==
                                _capacity['default_assistant_mode'],
                          ),
                        ),
                      )
                      .toList(),
                );
              },
            ),
            const SizedBox(height: 28),
            const _SectionTitle(
              title: 'Provider status',
              subtitle:
                  'ตรวจเฉพาะสถานะและชื่อตัวแปรที่ใช้ ไม่แสดงค่า API key',
            ),
            const SizedBox(height: 12),
            _ProviderPanel(providers: _providers),
            const SizedBox(height: 28),
            _SectionTitle(
              title: 'Brain Skills',
              subtitle: '${skills.length} provider-neutral skills พร้อม approval gate',
            ),
            const SizedBox(height: 12),
            LayoutBuilder(
              builder: (context, constraints) {
                final columns = constraints.maxWidth >= 1050
                    ? 3
                    : constraints.maxWidth >= 650
                        ? 2
                        : 1;
                final width =
                    (constraints.maxWidth - ((columns - 1) * 12)) / columns;
                if (skills.isEmpty && !_loading) {
                  return const Card(
                    child: Padding(
                      padding: EdgeInsets.all(18),
                      child: Text('ยังไม่พบ skill catalog จาก Local API'),
                    ),
                  );
                }
                return Wrap(
                  spacing: 12,
                  runSpacing: 12,
                  children: skills
                      .map(
                        (skill) => SizedBox(
                          width: width,
                          child: _SkillCard(skill: skill),
                        ),
                      )
                      .toList(),
                );
              },
            ),
            const SizedBox(height: 28),
            const _SectionTitle(
              title: 'Quick commands',
              subtitle: 'เรียกใช้ผ่าน AI Chat โดยเชื่อมกับ runtime เดิม',
            ),
            const SizedBox(height: 12),
            const Card(
              child: Padding(
                padding: EdgeInsets.all(18),
                child: Wrap(
                  spacing: 10,
                  runSpacing: 10,
                  children: <Widget>[
                    Chip(label: Text('ขอผู้ช่วย 6^3 วางแผนงานนี้')),
                    Chip(label: Text('ใช้สมอง 6^6 วิเคราะห์เชิงลึก')),
                    Chip(label: Text('เรียก API ค้นเว็บข้อมูลล่าสุด')),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ModeCard extends StatelessWidget {
  const _ModeCard({required this.mode, required this.selected});

  final Map<String, dynamic> mode;
  final bool selected;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final modeId = '${mode['mode'] ?? 'adaptive'}';
    final isSixCubed = modeId == 'assistant_6x3';
    final capacity = mode['theoretical_assistants'] ?? 0;
    final active = mode['recommended_max_active_workers'] ?? 0;
    return Card(
      key: Key('brain-mode-$modeId'),
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              children: <Widget>[
                Icon(isSixCubed ? Icons.groups_outlined : Icons.account_tree_outlined,
                    color: scheme.primary),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    isSixCubed ? 'ผู้ช่วย 6³' : 'สมองผสม 6⁶',
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),
                if (selected) const Chip(label: Text('Default')),
              ],
            ),
            const SizedBox(height: 12),
            Text('${mode['label'] ?? modeId}'),
            const SizedBox(height: 8),
            Text('$capacity theoretical slots • สูงสุด $active active workers'),
            const SizedBox(height: 6),
            const Text('เปิดใช้งานตาม demand • budget • readiness'),
          ],
        ),
      ),
    );
  }
}

class _ProviderPanel extends StatelessWidget {
  const _ProviderPanel({required this.providers});

  final Map<String, dynamic> providers;

  @override
  Widget build(BuildContext context) {
    final entries = providers.entries.toList();
    if (entries.isEmpty) {
      return const Card(
        child: Padding(
          padding: EdgeInsets.all(18),
          child: Text('ยังไม่พบ provider status จาก Local API'),
        ),
      );
    }
    return Card(
      child: Column(
        children: entries.map((entry) {
          final status = _BrainSkillsPageState._map(entry.value);
          final configured = status['configured'] == true;
          final source = '${status['credential_source'] ?? ''}'.trim();
          return ListTile(
            key: Key('brain-provider-${entry.key}'),
            leading: Icon(
              configured ? Icons.check_circle_outline : Icons.key_off_outlined,
              color: configured ? Colors.green : Theme.of(context).colorScheme.outline,
            ),
            title: Text(entry.key),
            subtitle: Text(
              configured && source.isNotEmpty
                  ? 'Configured via $source • secret hidden'
                  : configured
                      ? 'Configured • secret hidden'
                      : 'Not configured',
            ),
            trailing: Text(configured ? 'Configured' : 'Optional'),
          );
        }).toList(),
      ),
    );
  }
}

class _SkillCard extends StatelessWidget {
  const _SkillCard({required this.skill});

  final Map<String, dynamic> skill;

  @override
  Widget build(BuildContext context) {
    final guarded = skill['requires_approval_for_writes'] == true;
    return Card(
      key: Key('brain-skill-${skill['skill_id'] ?? 'unknown'}'),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              children: <Widget>[
                const Icon(Icons.extension_outlined, size: 20),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    '${skill['name'] ?? skill['skill_id'] ?? 'Brain Skill'}',
                    style: const TextStyle(fontWeight: FontWeight.w700),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text('${skill['description'] ?? ''}'),
            const SizedBox(height: 10),
            Text(
              guarded ? 'Approval required for writes' : 'Provider neutral',
              style: Theme.of(context).textTheme.labelMedium,
            ),
          ],
        ),
      ),
    );
  }
}

class _SectionTitle extends StatelessWidget {
  const _SectionTitle({required this.title, required this.subtitle});

  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Text(
          title,
          style: Theme.of(context)
              .textTheme
              .titleLarge
              ?.copyWith(fontWeight: FontWeight.w800),
        ),
        const SizedBox(height: 3),
        Text(subtitle),
      ],
    );
  }
}

class _StateBadge extends StatelessWidget {
  const _StateBadge({required this.label, required this.ready});

  final String label;
  final bool ready;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Chip(
      avatar: Icon(
        ready ? Icons.check_circle_outline : Icons.sync,
        size: 17,
        color: ready ? Colors.green : scheme.primary,
      ),
      label: Text(label),
    );
  }
}
