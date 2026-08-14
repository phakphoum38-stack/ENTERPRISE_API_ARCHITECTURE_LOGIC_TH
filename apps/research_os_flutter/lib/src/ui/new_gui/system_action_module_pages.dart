import 'package:flutter/material.dart';

import '../../platform/local_api_manager.dart';
import 'module_adapter_pages.dart';

class ResearchInstallerModulePage extends StatefulWidget {
  const ResearchInstallerModulePage({super.key});

  @override
  State<ResearchInstallerModulePage> createState() =>
      _ResearchInstallerModulePageState();
}

class _ResearchInstallerModulePageState
    extends State<ResearchInstallerModulePage> {
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
    return ResearchModuleSurface(
      title: 'Installer',
      subtitle:
          'Uses the existing installer/output candidate. Running Setup requests Windows elevation and waits for the installer exit code.',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          const _InfoPanel(
            icon: Icons.verified_user_outlined,
            title: 'Existing candidate only',
            body:
                'This page does not invent or rebuild Setup.exe. It opens or runs the latest Research-OS-Setup-*-x64.exe already produced by the repository candidate workflow.',
          ),
          const SizedBox(height: 16),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: <Widget>[
              OutlinedButton.icon(
                key: const Key('new-gui-installer-open-output'),
                onPressed: _working || !_manager.supported
                    ? null
                    : () => _run(_manager.openInstallerOutput),
                icon: const Icon(Icons.folder_open_outlined),
                label: const Text('Open installer output'),
              ),
              FilledButton.icon(
                key: const Key('new-gui-installer-run-latest'),
                onPressed: _working || !_manager.supported
                    ? null
                    : () => _run(_manager.runLatestInstaller),
                icon: _working
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.install_desktop_outlined),
                label: const Text('Run latest Setup.exe'),
              ),
            ],
          ),
          const SizedBox(height: 16),
          _OperationResultPanel(
            result: _result,
            idleText:
                'No installer action has been run from this page yet. The module reports success only from the actual Windows process exit code.',
          ),
        ],
      ),
    );
  }
}

class ResearchRestoreModulePage extends StatefulWidget {
  const ResearchRestoreModulePage({super.key});

  @override
  State<ResearchRestoreModulePage> createState() =>
      _ResearchRestoreModulePageState();
}

class _ResearchRestoreModulePageState extends State<ResearchRestoreModulePage> {
  final LocalApiManager _manager = const LocalApiManager();
  final TextEditingController _archiveController = TextEditingController();
  bool _working = false;
  LocalApiCommandResult? _result;

  @override
  void dispose() {
    _archiveController.dispose();
    super.dispose();
  }

  Future<void> _restore() async {
    if (_working || !_manager.supported) return;
    setState(() => _working = true);
    final result = await _manager.restore(_archiveController.text);
    if (!mounted) return;
    setState(() {
      _working = false;
      _result = result;
    });
  }

  @override
  Widget build(BuildContext context) {
    return ResearchModuleSurface(
      title: 'Restore',
      subtitle:
          'Restores a selected Research OS backup ZIP through scripts/restore-research-os.ps1. Existing restore logic remains the single implementation.',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          const _InfoPanel(
            icon: Icons.restore_outlined,
            title: 'Restore target',
            body:
                'The archive is expanded into the configured ResearchOSData directory. Existing files with the same names may be replaced by the restore script.',
          ),
          const SizedBox(height: 16),
          TextField(
            key: const Key('new-gui-restore-archive'),
            controller: _archiveController,
            enabled: !_working && _manager.supported,
            decoration: const InputDecoration(
              labelText: 'Backup ZIP path',
              hintText: r'C:\Users\you\ResearchOSData\backups\research-os-....zip',
              border: OutlineInputBorder(),
            ),
            onSubmitted: (_) => _restore(),
          ),
          const SizedBox(height: 12),
          Align(
            alignment: Alignment.centerLeft,
            child: FilledButton.icon(
              key: const Key('new-gui-restore-run'),
              onPressed:
                  _working || !_manager.supported ? null : _restore,
              icon: _working
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.restore_page_outlined),
              label: const Text('Restore backup'),
            ),
          ),
          const SizedBox(height: 16),
          _OperationResultPanel(
            result: _result,
            idleText:
                'No restore has been run yet. A missing archive is rejected before the PowerShell restore script is called.',
          ),
        ],
      ),
    );
  }
}

class ResearchShellModulePage extends StatefulWidget {
  const ResearchShellModulePage({super.key});

  @override
  State<ResearchShellModulePage> createState() =>
      _ResearchShellModulePageState();
}

class _ResearchShellModulePageState extends State<ResearchShellModulePage> {
  final LocalApiManager _manager = const LocalApiManager();
  final TextEditingController _commandController = TextEditingController();
  bool _working = false;
  LocalApiCommandResult? _result;

  @override
  void dispose() {
    _commandController.dispose();
    super.dispose();
  }

  Future<void> _runShell() async {
    if (_working || !_manager.supported) return;
    setState(() => _working = true);
    final result = await _manager.runShell(_commandController.text);
    if (!mounted) return;
    setState(() {
      _working = false;
      _result = result;
    });
  }

  @override
  Widget build(BuildContext context) {
    return ResearchModuleSurface(
      title: 'Shell',
      subtitle:
          'Runs an explicit PowerShell command as the current Windows user and returns the real stdout, stderr, and exit-code result.',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          const _InfoPanel(
            icon: Icons.terminal_outlined,
            title: 'Owner command surface',
            body:
                'Commands are not auto-elevated and are not silently rewritten. The working directory is the Research OS repository root when it can be resolved.',
          ),
          const SizedBox(height: 16),
          TextField(
            key: const Key('new-gui-shell-command'),
            controller: _commandController,
            enabled: !_working && _manager.supported,
            minLines: 3,
            maxLines: 8,
            decoration: const InputDecoration(
              labelText: 'PowerShell command',
              hintText: 'Get-Location',
              alignLabelWithHint: true,
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 12),
          Align(
            alignment: Alignment.centerLeft,
            child: FilledButton.icon(
              key: const Key('new-gui-shell-run'),
              onPressed:
                  _working || !_manager.supported ? null : _runShell,
              icon: _working
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.play_arrow_rounded),
              label: const Text('Run command'),
            ),
          ),
          const SizedBox(height: 16),
          _OperationResultPanel(
            result: _result,
            idleText:
                'No command has been run from this page yet. Output appears here after the PowerShell process exits.',
          ),
        ],
      ),
    );
  }
}

class _InfoPanel extends StatelessWidget {
  const _InfoPanel({
    required this.icon,
    required this.title,
    required this.body,
  });

  final IconData icon;
  final String title;
  final String body;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF11192B),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFF26344F)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Icon(icon, color: const Color(0xFF7EA2FF)),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  title,
                  style: const TextStyle(fontWeight: FontWeight.w800),
                ),
                const SizedBox(height: 5),
                Text(
                  body,
                  style: const TextStyle(
                    color: Color(0xFF9FB0C9),
                    height: 1.4,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _OperationResultPanel extends StatelessWidget {
  const _OperationResultPanel({
    required this.result,
    required this.idleText,
  });

  final LocalApiCommandResult? result;
  final String idleText;

  @override
  Widget build(BuildContext context) {
    final value = result;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF11192B),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFF26344F)),
      ),
      child: value == null
          ? Text(idleText)
          : Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Row(
                  children: <Widget>[
                    Icon(
                      value.ok
                          ? Icons.check_circle_outline
                          : Icons.error_outline,
                      color: value.ok
                          ? const Color(0xFF3DDC97)
                          : const Color(0xFFFF6B7A),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        value.message,
                        style: const TextStyle(fontWeight: FontWeight.w800),
                      ),
                    ),
                  ],
                ),
                if (value.details.trim().isNotEmpty) ...<Widget>[
                  const SizedBox(height: 10),
                  SelectableText(
                    value.details,
                    style: const TextStyle(fontFamily: 'monospace'),
                  ),
                ],
              ],
            ),
    );
  }
}
