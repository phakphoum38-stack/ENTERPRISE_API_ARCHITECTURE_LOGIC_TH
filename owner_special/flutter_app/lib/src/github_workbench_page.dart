import 'package:flutter/material.dart';

class GitHubWorkbenchPage extends StatefulWidget {
  const GitHubWorkbenchPage({super.key});

  @override
  State<GitHubWorkbenchPage> createState() => _GitHubWorkbenchPageState();
}

class _GitHubWorkbenchPageState extends State<GitHubWorkbenchPage> {
  int _section = 0;
  bool _dryRun = true;
  String _repository = 'ENTERPRISE_API_ARCHITECTURE_LOGIC_TH';
  final String _branch = 'feat/github-workbench';
  final _search = TextEditingController();

  static const _sections = <({IconData icon, String label})>[
    (icon: Icons.folder_outlined, label: 'Repository'),
    (icon: Icons.task_alt_outlined, label: 'Issues'),
    (icon: Icons.account_tree_outlined, label: 'Branches'),
    (icon: Icons.description_outlined, label: 'Files'),
    (icon: Icons.compare_arrows_outlined, label: 'Changes'),
    (icon: Icons.call_split_outlined, label: 'Pull Request'),
    (icon: Icons.verified_outlined, label: 'Checks'),
    (icon: Icons.policy_outlined, label: 'Authority'),
  ];

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return LayoutBuilder(
      builder: (context, constraints) {
        final compact = constraints.maxWidth < 1000;
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text('GitHub Workbench',
                      style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w700)),
                ),
                FilterChip(
                  key: const Key('github-dry-run'),
                  selected: _dryRun,
                  onSelected: (value) => setState(() => _dryRun = value),
                  avatar: Icon(_dryRun ? Icons.visibility_outlined : Icons.edit_outlined, size: 17),
                  label: Text(_dryRun ? 'DRY RUN' : 'LIVE'),
                ),
              ],
            ),
            const SizedBox(height: 4),
            Text(
              'Native GitHub work surface • every mutating action remains behind the Human Control Boundary',
              style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant),
            ),
            const SizedBox(height: 14),
            Expanded(
              child: Row(
                children: [
                  SizedBox(
                    width: compact ? 190 : 220,
                    child: Card(
                      child: ListView(
                        padding: const EdgeInsets.all(8),
                        children: [
                          for (var i = 0; i < _sections.length; i++)
                            ListTile(
                              dense: true,
                              selected: i == _section,
                              leading: Icon(_sections[i].icon, size: 19),
                              title: Text(_sections[i].label),
                              onTap: () => setState(() => _section = i),
                            ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(child: _buildSection(theme)),
                ],
              ),
            ),
          ],
        );
      },
    );
  }

  Widget _buildSection(ThemeData theme) {
    switch (_section) {
      case 0:
        return _repositoryPanel(theme);
      case 1:
        return _listPanel(theme, 'Issues', Icons.task_alt_outlined, const [
          ('Create Issue', 'Describe a new unit of work'),
          ('Open Issues', 'Review active work and ownership'),
          ('Search', 'Find issues across the selected repository'),
        ]);
      case 2:
        return _listPanel(theme, 'Branches', Icons.account_tree_outlined, const [
          ('Current branch', 'feat/github-workbench'),
          ('Create branch', 'Preview branch creation before execution'),
          ('Compare', 'Inspect branch ancestry and divergence'),
        ]);
      case 3:
        return _listPanel(theme, 'Files', Icons.description_outlined, const [
          ('Browse', 'Navigate repository files'),
          ('Open', 'Inspect source without leaving the OS'),
          ('Edit', 'Stage a proposed change for human approval'),
        ]);
      case 4:
        return _changesPanel(theme);
      case 5:
        return _listPanel(theme, 'Pull Request', Icons.call_split_outlined, const [
          ('Create PR', 'Choose base/head and preview the request'),
          ('Review', 'Inspect review state and discussion'),
          ('Merge', 'Only available after authority and repository gates'),
        ]);
      case 6:
        return _listPanel(theme, 'Checks', Icons.verified_outlined, const [
          ('CI status', 'Observe checks without bypassing them'),
          ('Evidence', 'Open run and artifact provenance'),
          ('Gate', 'Show merge readiness and blockers'),
        ]);
      default:
        return _authorityPanel(theme);
    }
  }

  Widget _repositoryPanel(ThemeData theme) {
    return Card(
      child: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Text('Repository', style: theme.textTheme.titleLarge),
          const SizedBox(height: 14),
          DropdownButtonFormField<String>(
            initialValue: _repository,
            decoration: const InputDecoration(labelText: 'Repository'),
            items: const [
              DropdownMenuItem(
                value: 'ENTERPRISE_API_ARCHITECTURE_LOGIC_TH',
                child: Text('phakphoum38-stack / ENTERPRISE_API_ARCHITECTURE_LOGIC_TH'),
              ),
            ],
            onChanged: (value) => setState(() => _repository = value ?? _repository),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _search,
            decoration: const InputDecoration(
              labelText: 'Universal GitHub search',
              hintText: 'issue, file, commit, PR…',
              prefixIcon: Icon(Icons.search),
            ),
          ),
          const SizedBox(height: 18),
          _statusTile(theme, Icons.account_tree_outlined, 'Branch', _branch),
          _statusTile(theme, Icons.cloud_done_outlined, 'Connection', 'GitHub adapter surface ready'),
          _statusTile(theme, Icons.visibility_outlined, 'Mutation mode', _dryRun ? 'Preview only' : 'Human approval required'),
          const SizedBox(height: 12),
          FilledButton.icon(
            onPressed: _dryRun ? null : () {},
            icon: const Icon(Icons.play_arrow_outlined),
            label: const Text('Execute approved action'),
          ),
        ],
      ),
    );
  }

  Widget _changesPanel(ThemeData theme) {
    return Card(
      child: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Text('Changes & Diff', style: theme.textTheme.titleLarge),
          const SizedBox(height: 8),
          Text('Prepare → inspect → approve → execute → observe → evidence',
              style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
          const SizedBox(height: 18),
          _statusTile(theme, Icons.edit_note_outlined, 'Working tree', 'Clean isolated Workbench base'),
          _statusTile(theme, Icons.commit_outlined, 'Proposed commit', 'Not created'),
          _statusTile(theme, Icons.call_split_outlined, 'Pull request', 'Not created'),
          const SizedBox(height: 12),
          OutlinedButton.icon(
            onPressed: () {},
            icon: const Icon(Icons.visibility_outlined),
            label: const Text('Preview diff'),
          ),
        ],
      ),
    );
  }

  Widget _authorityPanel(ThemeData theme) {
    return Card(
      child: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Text('Human Control Boundary', style: theme.textTheme.titleLarge),
          const SizedBox(height: 16),
          _authorityChip(theme, 'Observe', true),
          _authorityChip(theme, 'Analyze', true),
          _authorityChip(theme, 'Prepare', true),
          _authorityChip(theme, 'Approve', false),
          _authorityChip(theme, 'Authorize', false),
          _authorityChip(theme, 'Release / Merge', false),
          const Divider(height: 28),
          Text(
            'GitHub Workbench may prepare and explain an action, but it must not grant its own approval, authorization, or release authority.',
            style: theme.textTheme.bodyMedium,
          ),
        ],
      ),
    );
  }

  Widget _listPanel(ThemeData theme, String title, IconData icon, List<(String, String)> items) {
    return Card(
      child: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Row(children: [Icon(icon), const SizedBox(width: 10), Text(title, style: theme.textTheme.titleLarge)]),
          const SizedBox(height: 12),
          for (final item in items)
            Card(
              margin: const EdgeInsets.only(bottom: 8),
              child: ListTile(
                title: Text(item.$1),
                subtitle: Text(item.$2),
                trailing: const Icon(Icons.chevron_right),
                onTap: () {},
              ),
            ),
        ],
      ),
    );
  }

  Widget _statusTile(ThemeData theme, IconData icon, String label, String value) {
    return ListTile(
      contentPadding: EdgeInsets.zero,
      leading: Icon(icon),
      title: Text(label),
      subtitle: Text(value),
    );
  }

  Widget _authorityChip(ThemeData theme, String label, bool allowed) {
    return ListTile(
      contentPadding: EdgeInsets.zero,
      leading: Icon(allowed ? Icons.check_circle_outline : Icons.lock_outline),
      title: Text(label),
      subtitle: Text(allowed ? 'Available in Workbench' : 'Human authority required'),
    );
  }
}
