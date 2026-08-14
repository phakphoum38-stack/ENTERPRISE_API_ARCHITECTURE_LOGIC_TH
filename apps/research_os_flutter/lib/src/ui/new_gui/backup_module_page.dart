import 'package:flutter/material.dart';

import '../../platform/local_api_manager.dart';
import 'module_adapter_pages.dart';

class ResearchBackupModulePage extends StatefulWidget {
  const ResearchBackupModulePage({super.key});

  @override
  State<ResearchBackupModulePage> createState() =>
      _ResearchBackupModulePageState();
}

class _ResearchBackupModulePageState extends State<ResearchBackupModulePage> {
  final LocalApiManager _manager = const LocalApiManager();
  bool _working = false;
  LocalApiCommandResult? _result;

  Future<void> _run(Future<LocalApiCommandResult> Function() action) async {
    if (_working || !_manager.supported) return;
    setState(() => _working = true);
    final result = await action();
    if (!mounted) return;
    setState(() {
      _working = false;
      _result = result;
    });
  }

  @override
  Widget build(BuildContext context) {
    final result = _result;
    return ResearchModuleSurface(
      title: 'Backup',
      subtitle:
          'Uses the existing Research OS backup-research-os.ps1 path through LocalApiManager. The GUI does not create a second backup implementation.',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          Wrap(
            spacing: 12,
            runSpacing: 12,
            children: <Widget>[
              _BackupStatusCard(
                title: 'Platform',
                value: _manager.supported ? 'Windows ready' : 'Windows only',
                icon: Icons.desktop_windows_outlined,
              ),
              const _BackupStatusCard(
                title: 'Destination',
                value: 'ResearchOSData/backups',
                icon: Icons.folder_zip_outlined,
              ),
              const _BackupStatusCard(
                title: 'Format',
                value: 'Timestamped ZIP',
                icon: Icons.archive_outlined,
              ),
            ],
          ),
          const SizedBox(height: 18),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: <Widget>[
              FilledButton.icon(
                key: const Key('new-gui-backup-now'),
                onPressed: _working || !_manager.supported
                    ? null
                    : () => _run(_manager.backup),
                icon: _working
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.backup_outlined),
                label: const Text('Backup now'),
              ),
              OutlinedButton.icon(
                key: const Key('new-gui-backup-open-data'),
                onPressed: _working || !_manager.supported
                    ? null
                    : () => _run(_manager.openDataFolder),
                icon: const Icon(Icons.folder_open_outlined),
                label: const Text('Open data folder'),
              ),
            ],
          ),
          const SizedBox(height: 18),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: const Color(0xFF11192B),
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: const Color(0xFF26344F)),
            ),
            child: result == null
                ? const Text(
                    'No backup has been run from this page yet. Success is shown only after the existing backup script returns exit code 0.',
                  )
                : Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      Row(
                        children: <Widget>[
                          Icon(
                            result.ok
                                ? Icons.check_circle_outline
                                : Icons.error_outline,
                            color: result.ok
                                ? const Color(0xFF3DDC97)
                                : const Color(0xFFFF6B7A),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              result.message,
                              style: const TextStyle(fontWeight: FontWeight.w700),
                            ),
                          ),
                        ],
                      ),
                      if (result.details.trim().isNotEmpty) ...<Widget>[
                        const SizedBox(height: 10),
                        SelectableText(result.details),
                      ],
                    ],
                  ),
          ),
        ],
      ),
    );
  }
}

class _BackupStatusCard extends StatelessWidget {
  const _BackupStatusCard({
    required this.title,
    required this.value,
    required this.icon,
  });

  final String title;
  final String value;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 210,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFF11192B),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFF26344F)),
      ),
      child: Row(
        children: <Widget>[
          Icon(icon, color: const Color(0xFF7EA2FF)),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  title,
                  style: const TextStyle(
                    color: Color(0xFF8EA4C5),
                    fontSize: 10,
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  value,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontWeight: FontWeight.w700),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
