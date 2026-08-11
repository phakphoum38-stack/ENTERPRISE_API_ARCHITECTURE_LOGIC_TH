import 'package:flutter/material.dart';

import 'owner_api.dart';

class OwnerFriendApp extends StatefulWidget {
  const OwnerFriendApp({
    required this.api,
    this.startup,
    this.startupError,
    super.key,
  });

  final OwnerFriendApi api;
  final Map<String, dynamic>? startup;
  final String? startupError;

  @override
  State<OwnerFriendApp> createState() => _OwnerFriendAppState();
}

class _OwnerFriendAppState extends State<OwnerFriendApp> {
  int _index = 0;
  bool _railExtended = false;

  @override
  Widget build(BuildContext context) {
    final connected = widget.startupError == null;
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Research OS Friend',
      theme: ThemeData(
        useMaterial3: true,
        colorSchemeSeed: const Color(0xFF635BFF),
        scaffoldBackgroundColor: const Color(0xFFF8F8FB),
        cardTheme: const CardThemeData(
          elevation: 0,
          margin: EdgeInsets.zero,
          clipBehavior: Clip.antiAlias,
        ),
      ),
      home: Scaffold(
        body: SafeArea(
          child: Row(
            children: <Widget>[
              _SideRail(
                selectedIndex: _index,
                extended: _railExtended,
                connected: connected,
                onToggle: () => setState(() => _railExtended = !_railExtended),
                onSelected: (value) => setState(() => _index = value),
              ),
              const VerticalDivider(width: 1),
              Expanded(
                child: Column(
                  children: <Widget>[
                    _TopBar(
                      connected: connected,
                      section: const <String>['Chat', 'Capabilities', 'Memory', 'Provider'][_index],
                    ),
                    const Divider(height: 1),
                    Expanded(
                      child: IndexedStack(
                        index: _index,
                        children: <Widget>[
                          _FriendChatPage(api: widget.api),
                          _CapabilitiesPage(api: widget.api, startup: widget.startup),
                          _MemoryPage(api: widget.api),
                          _ProviderPage(api: widget.api),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _SideRail extends StatelessWidget {
  const _SideRail({
    required this.selectedIndex,
    required this.extended,
    required this.connected,
    required this.onToggle,
    required this.onSelected,
  });

  final int selectedIndex;
  final bool extended;
  final bool connected;
  final VoidCallback onToggle;
  final ValueChanged<int> onSelected;

  @override
  Widget build(BuildContext context) {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 180),
      width: extended ? 220 : 76,
      color: Theme.of(context).colorScheme.surface,
      child: Column(
        children: <Widget>[
          const SizedBox(height: 10),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 10),
            child: Row(
              children: <Widget>[
                IconButton(
                  tooltip: extended ? 'ย่อเมนู' : 'ขยายเมนู',
                  onPressed: onToggle,
                  icon: const Icon(Icons.menu),
                ),
                if (extended) ...<Widget>[
                  const SizedBox(width: 6),
                  const Expanded(
                    child: Text(
                      'Research OS',
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(fontWeight: FontWeight.w700),
                    ),
                  ),
                ],
              ],
            ),
          ),
          const SizedBox(height: 8),
          Expanded(
            child: NavigationRail(
              extended: extended,
              selectedIndex: selectedIndex,
              onDestinationSelected: onSelected,
              labelType: extended ? NavigationRailLabelType.none : NavigationRailLabelType.all,
              groupAlignment: -0.9,
              destinations: const <NavigationRailDestination>[
                NavigationRailDestination(
                  icon: Icon(Icons.chat_bubble_outline),
                  selectedIcon: Icon(Icons.chat_bubble),
                  label: Text('Friend'),
                ),
                NavigationRailDestination(
                  icon: Icon(Icons.auto_awesome_outlined),
                  selectedIcon: Icon(Icons.auto_awesome),
                  label: Text('Capabilities'),
                ),
                NavigationRailDestination(
                  icon: Icon(Icons.memory_outlined),
                  selectedIcon: Icon(Icons.memory),
                  label: Text('Memory'),
                ),
                NavigationRailDestination(
                  icon: Icon(Icons.tune_outlined),
                  selectedIcon: Icon(Icons.tune),
                  label: Text('Provider'),
                ),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(12),
            child: Tooltip(
              message: connected ? 'Friend Service connected' : 'Friend Service offline',
              child: Row(
                mainAxisAlignment: extended ? MainAxisAlignment.start : MainAxisAlignment.center,
                children: <Widget>[
                  Icon(
                    connected ? Icons.check_circle : Icons.error_outline,
                    size: 18,
                    color: connected ? Colors.green : Theme.of(context).colorScheme.error,
                  ),
                  if (extended) ...<Widget>[
                    const SizedBox(width: 8),
                    Text(connected ? 'Service online' : 'Service offline'),
                  ],
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _TopBar extends StatelessWidget {
  const _TopBar({required this.connected, required this.section});

  final bool connected;
  final String section;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 66,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 22),
        child: Row(
          children: <Widget>[
            Text(
              section,
              style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w700),
            ),
            const Spacer(),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.surfaceContainerHighest,
                borderRadius: BorderRadius.circular(999),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: <Widget>[
                  Icon(
                    connected ? Icons.link : Icons.link_off,
                    size: 16,
                  ),
                  const SizedBox(width: 6),
                  Text(connected ? 'Friend Service connected' : 'Friend Service offline'),
                ],
              ),
            ),
            const SizedBox(width: 10),
            const Chip(label: Text('UI V2')),
          ],
        ),
      ),
    );
  }
}

enum _QuickMode {
  normal,
  web,
  deepResearch,
  calendar,
  image,
  files,
  library,
}

extension _QuickModeUi on _QuickMode {
  String get title => switch (this) {
        _QuickMode.normal => 'ปกติ',
        _QuickMode.web => 'ค้นหาเว็บ',
        _QuickMode.deepResearch => 'หาข้อมูลเชิงลึก',
        _QuickMode.calendar => 'Google Calendar',
        _QuickMode.image => 'สร้างรูปภาพ',
        _QuickMode.files => 'เพิ่มรูปภาพและไฟล์',
        _QuickMode.library => 'เพิ่มจากคลัง',
      };

  String get subtitle => switch (this) {
        _QuickMode.normal => 'คุยกับ Friend โดยตรง',
        _QuickMode.web => 'เปิดโหมดงานวิจัยและค้นข้อมูลล่าสุด',
        _QuickMode.deepResearch => 'วิเคราะห์หลายขั้นและตรวจคุณภาพ',
        _QuickMode.calendar => 'เตรียมงานเกี่ยวกับกำหนดการ',
        _QuickMode.image => 'เตรียมคำขอสำหรับงานรูปภาพ',
        _QuickMode.files => 'เตรียมบริบทจากไฟล์บนเครื่อง',
        _QuickMode.library => 'เตรียมบริบทจากคลังความรู้',
      };

  IconData get icon => switch (this) {
        _QuickMode.normal => Icons.chat_bubble_outline,
        _QuickMode.web => Icons.language,
        _QuickMode.deepResearch => Icons.travel_explore,
        _QuickMode.calendar => Icons.calendar_month_outlined,
        _QuickMode.image => Icons.image_outlined,
        _QuickMode.files => Icons.attach_file,
        _QuickMode.library => Icons.library_books_outlined,
      };

  List<String> get skills => switch (this) {
        _QuickMode.normal => const <String>['analysis', 'planning', 'memory', 'quality'],
        _QuickMode.web => const <String>['research', 'analysis', 'quality'],
        _QuickMode.deepResearch => const <String>['research', 'analysis', 'planning', 'quality', 'memory'],
        _QuickMode.calendar => const <String>['automation', 'planning', 'memory'],
        _QuickMode.image => const <String>['planning', 'documents', 'quality'],
        _QuickMode.files => const <String>['documents', 'analysis', 'memory'],
        _QuickMode.library => const <String>['memory', 'documents', 'analysis'],
      };
}

class _ChatTurn {
  const _ChatTurn({required this.user, required this.answer, this.provider = '-'});

  final String user;
  final String answer;
  final String provider;
}

class _FriendChatPage extends StatefulWidget {
  const _FriendChatPage({required this.api});
  final OwnerFriendApi api;

  @override
  State<_FriendChatPage> createState() => _FriendChatPageState();
}

class _FriendChatPageState extends State<_FriendChatPage> {
  final _controller = TextEditingController();
  final _scrollController = ScrollController();
  final List<_ChatTurn> _turns = <_ChatTurn>[];

  bool _busy = false;
  bool _turboMillion = true;
  _QuickMode _mode = _QuickMode.normal;
  String _scale = '-';
  int _capacity = 0;
  int _activeWorkers = 0;
  int _batches = 0;
  String _factory = '-';
  String _provider = '-';

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _send() async {
    final text = _controller.text.trim();
    if (text.isEmpty || _busy) return;
    setState(() => _busy = true);
    try {
      final response = await widget.api.chat(
        text,
        complexity: _mode == _QuickMode.deepResearch ? 9 : 6,
        risk: 3,
        parallelism: _mode == _QuickMode.deepResearch ? 16 : 8,
        helperBudget: _turboMillion ? 1000000 : 0,
        requestedSkills: _mode.skills,
      );
      final decision = Map<String, dynamic>.from(response['decision'] as Map);
      final helpers = Map<String, dynamic>.from(response['helpers'] as Map? ?? const <String, dynamic>{});
      final factory = Map<String, dynamic>.from(response['factory'] as Map? ?? const <String, dynamic>{});
      final answer = response['text']?.toString() ?? '';
      final provider = response['provider']?.toString() ?? '-';
      setState(() {
        _turns.add(_ChatTurn(user: text, answer: answer, provider: provider));
        _provider = provider;
        _scale = decision['scale']?.toString() ?? '-';
        _capacity = (decision['capacity'] as num?)?.toInt() ?? 0;
        _activeWorkers = (helpers['active_workers'] as num?)?.toInt() ?? 0;
        _batches = (helpers['batches'] as num?)?.toInt() ?? 0;
        _factory = (factory['stages'] as List? ?? const <Object>[]).join(' → ');
        _controller.clear();
      });
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (_scrollController.hasClients) {
          _scrollController.animateTo(
            _scrollController.position.maxScrollExtent,
            duration: const Duration(milliseconds: 220),
            curve: Curves.easeOut,
          );
        }
      });
    } catch (error) {
      setState(() {
        _turns.add(_ChatTurn(user: text, answer: 'Friend Service error: $error'));
      });
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final contentWidth = constraints.maxWidth > 1180 ? 980.0 : constraints.maxWidth - 40;
        return Center(
          child: SizedBox(
            width: contentWidth.clamp(520, 980),
            child: Padding(
              padding: const EdgeInsets.fromLTRB(8, 18, 8, 18),
              child: Column(
                children: <Widget>[
                  _RuntimeStrip(
                    turboMillion: _turboMillion,
                    onTurboChanged: (value) => setState(() => _turboMillion = value),
                    scale: _scale,
                    capacity: _capacity,
                    workers: _activeWorkers,
                    batches: _batches,
                    provider: _provider,
                    factory: _factory,
                  ),
                  const SizedBox(height: 12),
                  Expanded(
                    child: _turns.isEmpty
                        ? _EmptyChat(mode: _mode)
                        : ListView.builder(
                            controller: _scrollController,
                            padding: const EdgeInsets.symmetric(vertical: 12),
                            itemCount: _turns.length,
                            itemBuilder: (context, index) => _ConversationTurn(turn: _turns[index]),
                          ),
                  ),
                  const SizedBox(height: 8),
                  _Composer(
                    controller: _controller,
                    busy: _busy,
                    mode: _mode,
                    onModeSelected: (value) => setState(() => _mode = value),
                    onSend: _send,
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }
}

class _RuntimeStrip extends StatelessWidget {
  const _RuntimeStrip({
    required this.turboMillion,
    required this.onTurboChanged,
    required this.scale,
    required this.capacity,
    required this.workers,
    required this.batches,
    required this.provider,
    required this.factory,
  });

  final bool turboMillion;
  final ValueChanged<bool> onTurboChanged;
  final String scale;
  final int capacity;
  final int workers;
  final int batches;
  final String provider;
  final String factory;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 42,
      child: ListView(
        scrollDirection: Axis.horizontal,
        children: <Widget>[
          FilterChip(
            key: const Key('turbo-million'),
            selected: turboMillion,
            onSelected: onTurboChanged,
            label: const Text('Turbo 1M'),
          ),
          const SizedBox(width: 8),
          Chip(label: Text('Brain $scale')),
          const SizedBox(width: 8),
          Chip(label: Text('Capacity $capacity')),
          const SizedBox(width: 8),
          Chip(label: Text('Workers $workers')),
          const SizedBox(width: 8),
          Chip(label: Text('Batches $batches')),
          if (provider != '-') ...<Widget>[
            const SizedBox(width: 8),
            Chip(avatar: const Icon(Icons.smart_toy_outlined, size: 16), label: Text(provider)),
          ],
          if (factory != '-') ...<Widget>[
            const SizedBox(width: 8),
            Chip(label: Text(factory)),
          ],
        ],
      ),
    );
  }
}

class _EmptyChat extends StatelessWidget {
  const _EmptyChat({required this.mode});
  final _QuickMode mode;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.only(bottom: 80),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            Container(
              width: 56,
              height: 56,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: Theme.of(context).colorScheme.primaryContainer,
              ),
              child: Icon(Icons.psychology, color: Theme.of(context).colorScheme.onPrimaryContainer),
            ),
            const SizedBox(height: 18),
            Text(
              'วันนี้ให้ Research OS Friend ช่วยอะไร?',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 8),
            Text(
              mode == _QuickMode.normal ? 'พร้อมคุย วิเคราะห์ วางแผน และใช้ความจำของ Owner' : 'โหมด ${mode.title}: ${mode.subtitle}',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: Theme.of(context).colorScheme.onSurfaceVariant),
            ),
          ],
        ),
      ),
    );
  }
}

class _ConversationTurn extends StatelessWidget {
  const _ConversationTurn({required this.turn});
  final _ChatTurn turn;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          Align(
            alignment: Alignment.centerRight,
            child: Container(
              constraints: const BoxConstraints(maxWidth: 700),
              padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.secondaryContainer,
                borderRadius: BorderRadius.circular(20),
              ),
              child: SelectableText(turn.user),
            ),
          ),
          const SizedBox(height: 18),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              CircleAvatar(
                radius: 16,
                backgroundColor: Theme.of(context).colorScheme.primaryContainer,
                child: Icon(Icons.psychology, size: 18, color: Theme.of(context).colorScheme.onPrimaryContainer),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    SelectableText(
                      turn.answer,
                      key: const Key('friend-answer'),
                      style: Theme.of(context).textTheme.bodyLarge?.copyWith(height: 1.55),
                    ),
                    if (turn.provider != '-') ...<Widget>[
                      const SizedBox(height: 8),
                      Text(
                        'Provider: ${turn.provider}',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Theme.of(context).colorScheme.onSurfaceVariant),
                      ),
                    ],
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _Composer extends StatelessWidget {
  const _Composer({
    required this.controller,
    required this.busy,
    required this.mode,
    required this.onModeSelected,
    required this.onSend,
  });

  final TextEditingController controller;
  final bool busy;
  final _QuickMode mode;
  final ValueChanged<_QuickMode> onModeSelected;
  final VoidCallback onSend;

  @override
  Widget build(BuildContext context) {
    return Material(
      elevation: 3,
      borderRadius: BorderRadius.circular(28),
      color: Theme.of(context).colorScheme.surface,
      child: Container(
        padding: const EdgeInsets.fromLTRB(10, 8, 10, 8),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(28),
          border: Border.all(color: Theme.of(context).colorScheme.outlineVariant),
        ),
        child: Column(
          children: <Widget>[
            if (mode != _QuickMode.normal)
              Align(
                alignment: Alignment.centerLeft,
                child: Padding(
                  padding: const EdgeInsets.only(left: 8, bottom: 4),
                  child: InputChip(
                    avatar: Icon(mode.icon, size: 17),
                    label: Text(mode.title),
                    onDeleted: () => onModeSelected(_QuickMode.normal),
                  ),
                ),
              ),
            Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: <Widget>[
                PopupMenuButton<_QuickMode>(
                  key: const Key('friend-tools-menu'),
                  tooltip: 'เพิ่มเครื่องมือ',
                  onSelected: onModeSelected,
                  position: PopupMenuPosition.over,
                  itemBuilder: (context) => _QuickMode.values
                      .where((item) => item != _QuickMode.normal)
                      .map(
                        (item) => PopupMenuItem<_QuickMode>(
                          value: item,
                          child: SizedBox(
                            width: 330,
                            child: Row(
                              children: <Widget>[
                                Icon(item.icon, size: 22),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    mainAxisSize: MainAxisSize.min,
                                    children: <Widget>[
                                      Text(item.title, style: const TextStyle(fontWeight: FontWeight.w600)),
                                      const SizedBox(height: 2),
                                      Text(item.subtitle, style: Theme.of(context).textTheme.bodySmall),
                                    ],
                                  ),
                                ),
                                if (mode == item) const Icon(Icons.check, size: 18),
                              ],
                            ),
                          ),
                        ),
                      )
                      .toList(),
                  child: Container(
                    width: 42,
                    height: 42,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: Theme.of(context).colorScheme.surfaceContainerHighest,
                    ),
                    child: const Icon(Icons.add),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: TextField(
                    key: const Key('friend-input'),
                    controller: controller,
                    minLines: 1,
                    maxLines: 6,
                    textInputAction: TextInputAction.newline,
                    onSubmitted: (_) => onSend(),
                    decoration: const InputDecoration(
                      border: InputBorder.none,
                      enabledBorder: InputBorder.none,
                      focusedBorder: InputBorder.none,
                      hintText: 'ถาม Research OS Friend…',
                      contentPadding: EdgeInsets.symmetric(horizontal: 6, vertical: 11),
                    ),
                  ),
                ),
                const SizedBox(width: 6),
                PopupMenuButton<_QuickMode>(
                  tooltip: 'โหมดการทำงาน',
                  onSelected: onModeSelected,
                  itemBuilder: (context) => _QuickMode.values
                      .map(
                        (item) => PopupMenuItem<_QuickMode>(
                          value: item,
                          child: Row(
                            children: <Widget>[
                              Icon(item.icon, size: 19),
                              const SizedBox(width: 9),
                              Text(item.title),
                              if (item == mode) ...<Widget>[
                                const Spacer(),
                                const Icon(Icons.check, size: 17),
                              ],
                            ],
                          ),
                        ),
                      )
                      .toList(),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 10),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: <Widget>[
                        Text(mode == _QuickMode.normal ? 'Normal' : mode.title),
                        const SizedBox(width: 3),
                        const Icon(Icons.keyboard_arrow_down, size: 18),
                      ],
                    ),
                  ),
                ),
                IconButton(
                  tooltip: 'ไมโครโฟน',
                  onPressed: busy ? null : () {},
                  icon: const Icon(Icons.mic_none),
                ),
                FilledButton(
                  key: const Key('friend-send'),
                  onPressed: busy ? null : onSend,
                  style: FilledButton.styleFrom(
                    shape: const CircleBorder(),
                    padding: const EdgeInsets.all(12),
                    minimumSize: const Size(44, 44),
                  ),
                  child: busy
                      ? const SizedBox.square(dimension: 18, child: CircularProgressIndicator(strokeWidth: 2))
                      : const Icon(Icons.arrow_upward, size: 20),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _CapabilitiesPage extends StatelessWidget {
  const _CapabilitiesPage({required this.api, this.startup});
  final OwnerFriendApi api;
  final Map<String, dynamic>? startup;

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<Map<String, dynamic>>(
      future: startup?['status'] is Map
          ? Future<Map<String, dynamic>>.value(Map<String, dynamic>.from(startup!['status'] as Map))
          : api.status(),
      builder: (context, snapshot) {
        if (!snapshot.hasData) return const Center(child: CircularProgressIndicator());
        final status = snapshot.data!;
        final profiles = Map<String, dynamic>.from(status['brain_profiles'] as Map? ?? const <String, dynamic>{});
        final helper = Map<String, dynamic>.from(status['helper_scheduler'] as Map? ?? const <String, dynamic>{});
        final capabilities = (status['capabilities'] as List? ?? const <Object>[]).map((item) => item.toString()).toList();
        return ListView(
          padding: const EdgeInsets.all(28),
          children: <Widget>[
            Text('Friend Complete Architecture', style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w700)),
            const SizedBox(height: 18),
            _InfoCard(
              title: 'Brain profiles',
              icon: Icons.psychology_outlined,
              child: Wrap(
                spacing: 8,
                runSpacing: 8,
                children: profiles.entries.map((entry) => Chip(label: Text('${entry.key} = ${entry.value}'))).toList(),
              ),
            ),
            const SizedBox(height: 14),
            _InfoCard(
              title: 'Helper scheduler',
              icon: Icons.hub_outlined,
              child: Text('Logical helpers: ${helper['max_logical_helpers'] ?? '-'}  •  Active workers: ${helper['max_active_workers'] ?? '-'}'),
            ),
            const SizedBox(height: 14),
            _InfoCard(
              title: 'Capabilities',
              icon: Icons.auto_awesome_outlined,
              child: Wrap(
                spacing: 8,
                runSpacing: 8,
                children: capabilities.map((name) => Chip(label: Text(name))).toList(),
              ),
            ),
          ],
        );
      },
    );
  }
}

class _InfoCard extends StatelessWidget {
  const _InfoCard({required this.title, required this.icon, required this.child});
  final String title;
  final IconData icon;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              children: <Widget>[
                Icon(icon),
                const SizedBox(width: 10),
                Text(title, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
              ],
            ),
            const SizedBox(height: 14),
            child,
          ],
        ),
      ),
    );
  }
}

class _MemoryPage extends StatelessWidget {
  const _MemoryPage({required this.api});
  final OwnerFriendApi api;

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<Map<String, dynamic>>(
      future: api.memory(),
      builder: (context, snapshot) {
        if (!snapshot.hasData) return const Center(child: CircularProgressIndicator());
        final items = snapshot.data!['items'] as List? ?? const <Object>[];
        if (items.isEmpty) {
          return const Center(child: Text('ยังไม่มีความจำใน profile/session นี้'));
        }
        return ListView.separated(
          padding: const EdgeInsets.all(28),
          itemCount: items.length,
          separatorBuilder: (_, __) => const SizedBox(height: 10),
          itemBuilder: (context, index) {
            final item = Map<String, dynamic>.from(items[index] as Map);
            final kind = item['kind']?.toString() ?? '';
            final text = item['text']?.toString() ?? '';
            return Card(
              child: ListTile(
                leading: CircleAvatar(child: Icon(kind == 'request' ? Icons.person_outline : Icons.psychology_outlined)),
                title: Text(kind.isEmpty ? 'memory' : kind),
                subtitle: Text(text),
              ),
            );
          },
        );
      },
    );
  }
}

class _ProviderPage extends StatefulWidget {
  const _ProviderPage({required this.api});
  final OwnerFriendApi api;

  @override
  State<_ProviderPage> createState() => _ProviderPageState();
}

class _ProviderPageState extends State<_ProviderPage> {
  final _baseUrl = TextEditingController();
  final _model = TextEditingController();
  final _apiKey = TextEditingController();
  Map<String, dynamic>? _status;
  String _message = '';
  bool _busy = false;
  bool _revealKey = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _baseUrl.dispose();
    _model.dispose();
    _apiKey.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    try {
      final status = await widget.api.providerStatus();
      if (!mounted) return;
      setState(() {
        _status = status;
        _baseUrl.text = status['base_url']?.toString() ?? '';
        _model.text = status['model']?.toString() ?? '';
      });
    } catch (error) {
      if (mounted) setState(() => _message = '$error');
    }
  }

  Future<void> _saveAndTest() async {
    if (_busy) return;
    setState(() {
      _busy = true;
      _message = '';
    });
    try {
      final saved = await widget.api.configureProvider(
        baseUrl: _baseUrl.text.trim(),
        model: _model.text.trim(),
        apiKey: _apiKey.text.trim().isEmpty ? null : _apiKey.text.trim(),
      );
      _apiKey.clear();
      final tested = await widget.api.testProvider();
      if (!mounted) return;
      setState(() {
        _status = saved;
        _message = tested['connected'] == true
            ? 'Provider connected'
            : 'Provider test failed: ${tested['error'] ?? 'unknown'}';
      });
    } catch (error) {
      if (mounted) setState(() => _message = '$error');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final credentialPresent = _status?['credential_present'] == true;
    return Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 760),
        child: ListView(
          padding: const EdgeInsets.all(28),
          children: <Widget>[
            Text('AI Provider', style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            Text(
              'เชื่อม OpenAI-compatible API เพื่อให้ Friend ตอบด้วยโมเดล AI จริง',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: Theme.of(context).colorScheme.onSurfaceVariant),
            ),
            const SizedBox(height: 18),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: <Widget>[
                    Row(
                      children: <Widget>[
                        Icon(credentialPresent ? Icons.lock : Icons.lock_open_outlined),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            credentialPresent ? 'API key stored securely' : 'API key not configured',
                            style: const TextStyle(fontWeight: FontWeight.w600),
                          ),
                        ),
                        Chip(label: Text('${_status?['secret_backend'] ?? '-'}')),
                      ],
                    ),
                    const SizedBox(height: 18),
                    TextField(
                      key: const Key('provider-base-url'),
                      controller: _baseUrl,
                      decoration: const InputDecoration(labelText: 'Base URL', border: OutlineInputBorder()),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      key: const Key('provider-model'),
                      controller: _model,
                      decoration: const InputDecoration(labelText: 'Model', border: OutlineInputBorder()),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      key: const Key('provider-api-key'),
                      controller: _apiKey,
                      obscureText: !_revealKey,
                      decoration: InputDecoration(
                        labelText: 'API key (เว้นว่างเพื่อใช้คีย์เดิม)',
                        border: const OutlineInputBorder(),
                        suffixIcon: IconButton(
                          onPressed: () => setState(() => _revealKey = !_revealKey),
                          icon: Icon(_revealKey ? Icons.visibility_off_outlined : Icons.visibility_outlined),
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                    FilledButton.icon(
                      key: const Key('provider-save-test'),
                      onPressed: _busy ? null : _saveAndTest,
                      icon: _busy
                          ? const SizedBox.square(dimension: 18, child: CircularProgressIndicator(strokeWidth: 2))
                          : const Icon(Icons.link),
                      label: const Text('Save & Test Connection'),
                    ),
                    if (_message.isNotEmpty)
                      Padding(
                        padding: const EdgeInsets.only(top: 16),
                        child: SelectableText(_message, key: const Key('provider-message')),
                      ),
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
