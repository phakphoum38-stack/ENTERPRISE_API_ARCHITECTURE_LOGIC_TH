import 'package:flutter/material.dart';

class TeamMember {
  const TeamMember({required this.userId, required this.displayName, required this.role});
  final String userId;
  final String displayName;
  final String role;
}

class TeamWorkspace {
  const TeamWorkspace({required this.id, required this.name, required this.members});
  final String id;
  final String name;
  final List<TeamMember> members;
}

class TeamCenter extends StatefulWidget {
  const TeamCenter({super.key, this.isOwner = true, this.onChanged});
  final bool isOwner;
  final ValueChanged<TeamWorkspace>? onChanged;

  @override
  State<TeamCenter> createState() => _TeamCenterState();
}

class _TeamCenterState extends State<TeamCenter> {
  final List<TeamWorkspace> _teams = <TeamWorkspace>[
    const TeamWorkspace(
      id: 'research',
      name: 'Research Team',
      members: <TeamMember>[
        TeamMember(userId: 'owner', displayName: 'Owner', role: 'owner'),
      ],
    ),
    const TeamWorkspace(
      id: 'engineering',
      name: 'Engineering Team',
      members: <TeamMember>[],
    ),
    const TeamWorkspace(
      id: 'ai',
      name: 'AI Team',
      members: <TeamMember>[],
    ),
  ];

  String _selectedId = 'research';

  TeamWorkspace get _selected => _teams.firstWhere((team) => team.id == _selectedId);

  void _selectTeam(String id) {
    setState(() => _selectedId = id);
    widget.onChanged?.call(_selected);
  }

  Future<void> _createTeam() async {
    if (!widget.isOwner) return;
    final controller = TextEditingController();
    final name = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Create New Team'),
        content: TextField(
          controller: controller,
          autofocus: true,
          decoration: const InputDecoration(labelText: 'Team name'),
          onSubmitted: (_) => Navigator.of(context).pop(controller.text.trim()),
        ),
        actions: <Widget>[
          TextButton(onPressed: () => Navigator.of(context).pop(), child: const Text('Cancel')),
          FilledButton(onPressed: () => Navigator.of(context).pop(controller.text.trim()), child: const Text('Create')),
        ],
      ),
    );
    controller.dispose();
    if (!mounted || name == null || name.trim().isEmpty) return;
    final id = 'team-${DateTime.now().microsecondsSinceEpoch}';
    final created = TeamWorkspace(
      id: id,
      name: name.trim(),
      members: const <TeamMember>[TeamMember(userId: 'owner', displayName: 'Owner', role: 'owner')],
    );
    setState(() {
      _teams.add(created);
      _selectedId = id;
    });
    widget.onChanged?.call(created);
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            Row(
              children: <Widget>[
                const Icon(Icons.groups_outlined),
                const SizedBox(width: 8),
                Expanded(child: Text('Team Center', style: Theme.of(context).textTheme.titleLarge)),
                if (widget.isOwner)
                  IconButton(tooltip: 'Create Team', onPressed: _createTeam, icon: const Icon(Icons.add)),
              ],
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              key: const Key('team-switcher'),
              initialValue: _selectedId,
              decoration: const InputDecoration(labelText: 'Current Team', border: OutlineInputBorder()),
              items: _teams.map((team) => DropdownMenuItem<String>(value: team.id, child: Text(team.name))).toList(),
              onChanged: (value) {
                if (value != null) _selectTeam(value);
              },
            ),
            const SizedBox(height: 12),
            Text('Team ID: ${_selected.id}'),
            Text('Members: ${_selected.members.length}'),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              children: <Widget>[
                Chip(label: Text('Chat: ${_selected.id}')),
                Chip(label: Text('Agents: ${_selected.id}')),
                Chip(label: Text('Memory: ${_selected.id}')),
                Chip(label: Text('Files: ${_selected.id}')),
                Chip(label: Text('Tasks: ${_selected.id}')),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
