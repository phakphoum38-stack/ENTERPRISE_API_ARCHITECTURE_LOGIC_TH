import 'dart:async';

import 'package:flutter/material.dart';

import '../models/system_snapshot.dart';
import '../services/installer_service.dart';
import 'chat_page.dart';
import 'drive_page.dart';
import 'files_page.dart';
import 'logs_page.dart';
import 'overview_page.dart';
import 'providers_page.dart';
import 'repositories_page.dart';
import 'restore_page.dart';
import 'settings_page.dart';
import 'sync_page.dart';

class ShellPage extends StatefulWidget {
  const ShellPage({super.key});

  @override
  State<ShellPage> createState() => _ShellPageState();
}

class _ShellPageState extends State<ShellPage> {
  final _installer = InstallerService();
  SystemSnapshot? _snapshot;
  int _selected = 0;
  bool _railExpanded = true;
  bool _busy = false;
  String _notice = 'กำลังตรวจสอบ Research OS…';
  Timer? _timer;

  static const _items = <_NavItem>[
    _NavItem('ภาพรวม', Icons.space_dashboard_outlined, Icons.space_dashboard),
    _NavItem('AI Chat', Icons.chat_bubble_outline, Icons.chat_bubble),
    _NavItem('Repositories', Icons.folder_copy_outlined, Icons.folder_copy),
    _NavItem('Files', Icons.folder_outlined, Icons.folder),
    _NavItem('API Providers', Icons.key_outlined, Icons.key),
    _NavItem('Drive Root', Icons.cloud_outlined, Icons.cloud),
    _NavItem('Sync / Mirror', Icons.sync_outlined, Icons.sync),
    _NavItem('Restore', Icons.settings_backup_restore_outlined, Icons.settings_backup_restore),
    _NavItem('Logs', Icons.terminal_outlined, Icons.terminal),
    _NavItem('Settings', Icons.settings_outlined, Icons.settings),
  ];

  @override
  void initState() {
    super.initState();
    _refresh();
    _timer = Timer.periodic(const Duration(seconds: 20), (_) => _refresh(silent: true));
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _refresh({bool silent = false}) async {
    if (!silent && mounted) setState(() => _notice = 'กำลังตรวจสอบระบบ…');
    try {
      final snapshot = await _installer.inspectSystem();
      if (!mounted) return;
      setState(() {
        _snapshot = snapshot;
        if (!silent) _notice = 'ตรวจสอบล่าสุดแล้ว';
      });
    } catch (e) {
      if (mounted) setState(() => _notice = 'ตรวจสอบไม่สำเร็จ: $e');
    }
  }

  Future<void> _perform(Future<String> Function() action) async {
    setState(() => _busy = true);
    try {
      final message = await action();
      if (!mounted) return;
      setState(() => _notice = message);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
      await _refresh(silent: true);
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$e')));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final compact = MediaQuery.sizeOf(context).width < 980;
    return Scaffold(
      drawer: compact ? Drawer(child: SafeArea(child: _DrawerMenu(items: _items, selected: _selected, onSelected: (i) { Navigator.pop(context); setState(() => _selected = i); }))) : null,
      body: SafeArea(
        child: Row(
          children: [
            if (!compact) ...[
              NavigationRail(
                selectedIndex: _selected,
                extended: _railExpanded,
                minWidth: 72,
                minExtendedWidth: 220,
                labelType: _railExpanded ? NavigationRailLabelType.none : NavigationRailLabelType.all,
                leading: Padding(
                  padding: const EdgeInsets.only(top: 14, bottom: 20),
                  child: Row(mainAxisSize: MainAxisSize.min, children: [const CircleAvatar(child: Icon(Icons.science_outlined)), if (_railExpanded) ...[const SizedBox(width: 10), const Text('Research OS', style: TextStyle(fontWeight: FontWeight.w800))]]),
                ),
                trailing: Expanded(child: Align(alignment: Alignment.bottomCenter, child: Padding(padding: const EdgeInsets.only(bottom: 16), child: IconButton.filledTonal(onPressed: () => setState(() => _railExpanded = !_railExpanded), icon: Icon(_railExpanded ? Icons.keyboard_double_arrow_left : Icons.keyboard_double_arrow_right))))),
                destinations: _items.map((item) => NavigationRailDestination(icon: Icon(item.icon), selectedIcon: Icon(item.selectedIcon), label: Text(item.label))).toList(),
                onDestinationSelected: (i) => setState(() => _selected = i),
              ),
              const VerticalDivider(width: 1),
            ],
            Expanded(
              child: Column(
                children: [
                  _TopBar(compact: compact, notice: _notice, snapshot: _snapshot, busy: _busy, onRefresh: _refresh),
                  const Divider(height: 1),
                  Expanded(child: AnimatedSwitcher(duration: const Duration(milliseconds: 160), child: KeyedSubtree(key: ValueKey(_selected), child: _page()))),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _page() {
    switch (_selected) {
      case 1:
        return const ChatPage();
      case 2:
        return RepositoriesPage(snapshot: _snapshot);
      case 3:
        return FilesPage(snapshot: _snapshot);
      case 4:
        return const ProvidersPage();
      case 5:
        return DrivePage(snapshot: _snapshot, onInstall: () => _perform(_installer.install), onOpenRoot: () => _installer.openRoot(_snapshot?.rootPath), onRefresh: _refresh);
      case 6:
        return SyncPage(snapshot: _snapshot, onStart: () => _perform(_installer.runMirrorWorker), onStop: () => _perform(_installer.stopMirrorWorker), onLogin: () => _perform(_installer.openGithubLogin), onOpenBundles: () => _installer.openRelativeFolder('github\\bundles\\full', _snapshot?.rootPath), onOpenMirrors: () => _installer.openRelativeFolder('github\\mirrors\\bare', _snapshot?.rootPath));
      case 7:
        return RestorePage(snapshot: _snapshot);
      case 8:
        return LogsPage(snapshot: _snapshot, onRefresh: _refresh, onOpenLogs: () => _installer.openRelativeFolder('logs\\github', _snapshot?.rootPath));
      case 9:
        return SettingsPage(onChanged: _refresh);
      default:
        return OverviewPage(snapshot: _snapshot, onInstall: () => _perform(_installer.install), onSync: () => _perform(_installer.runMirrorWorker), onOpenRoot: () => _installer.openRoot(_snapshot?.rootPath), onNavigate: (i) => setState(() => _selected = i));
    }
  }
}

class _TopBar extends StatelessWidget {
  const _TopBar({required this.compact, required this.notice, required this.snapshot, required this.busy, required this.onRefresh});
  final bool compact;
  final String notice;
  final SystemSnapshot? snapshot;
  final bool busy;
  final VoidCallback onRefresh;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 66,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16),
        child: Row(
          children: [
            if (compact) Builder(builder: (context) => IconButton(onPressed: () => Scaffold.of(context).openDrawer(), icon: const Icon(Icons.menu))),
            if (busy) const Padding(padding: EdgeInsets.only(right: 12), child: SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))),
            Expanded(child: Text(notice, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(color: Colors.white60))),
            _TinyStatus(label: 'ROOT', good: snapshot?.rootReady == true),
            const SizedBox(width: 6),
            _TinyStatus(label: 'GITHUB', good: snapshot?.githubAuthenticated == true),
            const SizedBox(width: 6),
            _TinyStatus(label: 'WORKER', good: snapshot?.workerInstalled == true),
            const SizedBox(width: 8),
            IconButton(onPressed: onRefresh, tooltip: 'Refresh', icon: const Icon(Icons.refresh)),
          ],
        ),
      ),
    );
  }
}

class _TinyStatus extends StatelessWidget {
  const _TinyStatus({required this.label, required this.good});
  final String label;
  final bool good;
  @override
  Widget build(BuildContext context) {
    final color = good ? Colors.greenAccent : Colors.orangeAccent;
    return Container(padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 5), decoration: BoxDecoration(color: color.withValues(alpha: .08), borderRadius: BorderRadius.circular(999), border: Border.all(color: color.withValues(alpha: .22))), child: Row(mainAxisSize: MainAxisSize.min, children: [Container(width: 6, height: 6, decoration: BoxDecoration(color: color, shape: BoxShape.circle)), const SizedBox(width: 5), Text(label, style: TextStyle(color: color, fontSize: 10, fontWeight: FontWeight.w800))]));
  }
}

class _DrawerMenu extends StatelessWidget {
  const _DrawerMenu({required this.items, required this.selected, required this.onSelected});
  final List<_NavItem> items;
  final int selected;
  final ValueChanged<int> onSelected;
  @override
  Widget build(BuildContext context) {
    return ListView(padding: const EdgeInsets.all(12), children: [const ListTile(leading: CircleAvatar(child: Icon(Icons.science_outlined)), title: Text('Research OS', style: TextStyle(fontWeight: FontWeight.w800)), subtitle: Text('Full Control Center')), const Divider(), ...List.generate(items.length, (i) => ListTile(selected: selected == i, leading: Icon(selected == i ? items[i].selectedIcon : items[i].icon), title: Text(items[i].label), onTap: () => onSelected(i)))]);
  }
}

class _NavItem {
  const _NavItem(this.label, this.icon, this.selectedIcon);
  final String label;
  final IconData icon;
  final IconData selectedIcon;
}
