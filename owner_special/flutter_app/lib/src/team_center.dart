import 'package:flutter/material.dart';

class TeamMember {
  const TeamMember({required this.userId, required this.displayName, required this.role});
  final String userId;
  final String displayName;
  final String role;
}

class TeamWorkspace {
  const TeamWorkspace({required this.id, required this.name, this.members = const <TeamMember>[]});
  final String id;
  final String name;
  final List<TeamMember> members;
}

typedef TeamRecord = TeamWorkspace;

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
    const TeamWorkspace(id: 'engineering', name: 'Engineering Team'),
    const TeamWorkspace(id: 'ai', name: 'AI Team'),
  ];

  String _selectedId = 'research';

  TeamWorkspace get _selected => _teams.firstWhere((team) => team.id == _selectedId);

  void _selectTeam(String? id) {
    if (id == null || id == _selectedId) return;
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

    // Do not mutate the TeamCenter render tree in the same frame as the dialog
    // route is removed. Flutter's semantics pass can otherwise observe dirty
    // parentData and fail widget tests during pumpAndSettle.
    await Future<void>.delayed(Duration.zero);
    if (!mounted) return;

    final id = 'team-${DateTime.now().microsecondsSinceEpoch}';
    final created = TeamWorkspace(
      id: id,
      name: name.trim(),
      members: const <TeamMember>[
        TeamMember(userId: 'owner', displayName: 'Owner', role: 'owner'),
      ],
    );
    if (!mounted) return;
    setState(() {
      _teams.add(created);
      _selectedId = id;
    });
    widget.onChanged?.call(created);
  }

  @override
  Widget build(BuildContext context) {
    final selected = _selected;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          children: <Widget>[
            const Icon(Icons.groups_outlined),
            const SizedBox(width: 8),
            Expanded(
              child: DropdownButton<String>(
                key: const Key('team-switcher'),
                value: _selectedId,
                isExpanded: true,
                onChanged: _selectTeam,
                items: _teams
                    .map((team) => DropdownMenuItem<String>(
                          value: team.id,
                          child: Text(team.name),
                        ))
                    .toList(),
              ),
            ),
            const SizedBox(width: 8),
            Text('Members: ${selected.members.length}'),
            if (widget.isOwner)
              IconButton(
                tooltip: 'Create Team',
                onPressed: _createTeam,
                icon: const Icon(Icons.add),
              ),
          ],
        ),
      ),
    );
  }
}
