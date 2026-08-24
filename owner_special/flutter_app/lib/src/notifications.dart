import 'package:flutter/material.dart';

enum OwnerNotificationLevel { info, success, warning, error }

final class OwnerNotificationEntry {
  const OwnerNotificationEntry({
    required this.id,
    required this.title,
    required this.message,
    required this.level,
    required this.createdAt,
  });

  final int id;
  final String title;
  final String message;
  final OwnerNotificationLevel level;
  final DateTime createdAt;
}

final class OwnerNotificationCenter extends ChangeNotifier {
  OwnerNotificationCenter._();

  static final OwnerNotificationCenter instance = OwnerNotificationCenter._();

  final List<OwnerNotificationEntry> _items = <OwnerNotificationEntry>[];
  int _nextId = 1;
  int _unreadCount = 0;

  List<OwnerNotificationEntry> get items => List<OwnerNotificationEntry>.unmodifiable(_items);
  int get unreadCount => _unreadCount;

  void startSession({required bool serviceConnected, String? startupError}) {
    _items.clear();
    _unreadCount = 0;
    _nextId = 1;
    add(
      level: serviceConnected ? OwnerNotificationLevel.success : OwnerNotificationLevel.error,
      title: serviceConnected ? 'Friend Service connected' : 'Friend Service offline',
      message: serviceConnected
          ? 'Owner Friend service is ready on this desktop session.'
          : (startupError?.trim().isNotEmpty == true ? startupError!.trim() : 'Unable to reach Owner Friend service.'),
    );
  }

  void addInfo(String title, String message) => add(level: OwnerNotificationLevel.info, title: title, message: message);
  void addSuccess(String title, String message) => add(level: OwnerNotificationLevel.success, title: title, message: message);
  void addWarning(String title, String message) => add(level: OwnerNotificationLevel.warning, title: title, message: message);
  void addError(String title, String message) => add(level: OwnerNotificationLevel.error, title: title, message: message);

  void add({required OwnerNotificationLevel level, required String title, required String message}) {
    _items.insert(
      0,
      OwnerNotificationEntry(
        id: _nextId++,
        title: title,
        message: message,
        level: level,
        createdAt: DateTime.now(),
      ),
    );
    _unreadCount += 1;
    notifyListeners();
  }

  void markAllRead() {
    if (_unreadCount == 0) return;
    _unreadCount = 0;
    notifyListeners();
  }

  void clear() {
    if (_items.isEmpty && _unreadCount == 0) return;
    _items.clear();
    _unreadCount = 0;
    notifyListeners();
  }
}

class OwnerNotificationsPage extends StatelessWidget {
  const OwnerNotificationsPage({required this.center, super.key});

  final OwnerNotificationCenter center;

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: center,
      builder: (context, _) {
        final items = center.items;
        return Column(
          children: <Widget>[
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 20, 24, 12),
              child: Row(
                children: <Widget>[
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Text('Notifications', style: Theme.of(context).textTheme.headlineSmall),
                        const SizedBox(height: 4),
                        Text('${items.length} events • ${center.unreadCount} unread'),
                      ],
                    ),
                  ),
                  TextButton.icon(
                    key: const Key('notifications-mark-read'),
                    onPressed: center.unreadCount == 0 ? null : center.markAllRead,
                    icon: const Icon(Icons.done_all),
                    label: const Text('Mark all read'),
                  ),
                  const SizedBox(width: 8),
                  OutlinedButton.icon(
                    key: const Key('notifications-clear'),
                    onPressed: items.isEmpty ? null : center.clear,
                    icon: const Icon(Icons.delete_sweep_outlined),
                    label: const Text('Clear'),
                  ),
                ],
              ),
            ),
            const Divider(height: 1),
            Expanded(
              child: items.isEmpty
                  ? const Center(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: <Widget>[
                          Icon(Icons.notifications_none, size: 48),
                          SizedBox(height: 12),
                          Text('No notifications yet'),
                        ],
                      ),
                    )
                  : ListView.separated(
                      padding: const EdgeInsets.all(16),
                      itemCount: items.length,
                      separatorBuilder: (_, __) => const SizedBox(height: 8),
                      itemBuilder: (context, index) {
                        final item = items[index];
                        return Card(
                          child: ListTile(
                            key: Key('notification-${item.id}'),
                            leading: Icon(_iconFor(item.level)),
                            title: Text(item.title),
                            subtitle: Padding(
                              padding: const EdgeInsets.only(top: 4),
                              child: Text('${item.message}\n${_formatTime(item.createdAt)}'),
                            ),
                            isThreeLine: true,
                          ),
                        );
                      },
                    ),
            ),
          ],
        );
      },
    );
  }

  static IconData _iconFor(OwnerNotificationLevel level) => switch (level) {
        OwnerNotificationLevel.info => Icons.info_outline,
        OwnerNotificationLevel.success => Icons.check_circle_outline,
        OwnerNotificationLevel.warning => Icons.warning_amber_rounded,
        OwnerNotificationLevel.error => Icons.error_outline,
      };

  static String _formatTime(DateTime value) {
    String two(int number) => number.toString().padLeft(2, '0');
    return '${two(value.hour)}:${two(value.minute)}:${two(value.second)}';
  }
}
