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

class TeamVisual {
  const TeamVisual({required this.primary, required this.secondary, required this.icon});
  final Color primary;
  final Color secondary;
  final IconData icon;
}

TeamVisual teamVisual(String id) {
  switch (id) {
    case 'engineering':
      return const TeamVisual(primary: Color(0xFF34D399), secondary: Color(0xFF06B6D4), icon: Icons.precision_manufacturing_outlined);
    case 'ai':
      return const TeamVisual(primary: Color(0xFFA78BFA), secondary: Color(0xFFF472B6), icon: Icons.auto_awesome_outlined);
    case 'research':
    default:
      return const TeamVisual(primary: Color(0xFF38BDF8), secondary: Color(0xFF818CF8), icon: Icons.science_outlined);
  }
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
    final name = await showDialog<String>(
      context: context,
      builder: (context) => const _CreateTeamDialog(),
    );
    if (!mounted || name == null || name.trim().isEmpty) return;

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
    setState(() {
      _teams.add(created);
      _selectedId = id;
    });
    widget.onChanged?.call(created);
  }

  @override
  Widget build(BuildContext context) {
    final selected = _selected;
    final visual = teamVisual(selected.id);
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(18),
        color: Theme.of(context).colorScheme.surface.withValues(alpha: .72),
        border: Border.all(color: visual.primary.withValues(alpha: .22)),
        boxShadow: [BoxShadow(color: visual.secondary.withValues(alpha: .10), blurRadius: 20, spreadRadius: 1)],
      ),
      child: Row(
        children: <Widget>[
          _TeamOrb(visual: visual, size: 42),
          const SizedBox(width: 10),
          Expanded(
            child: DropdownButtonHideUnderline(
              child: DropdownButton<String>(
                key: const Key('team-switcher'),
                value: _selectedId,
                isExpanded: true,
                onChanged: _selectTeam,
                dropdownColor: Theme.of(context).colorScheme.surface,
                items: _teams.map((team) {
                  final itemVisual = teamVisual(team.id);
                  return DropdownMenuItem<String>(
                    value: team.id,
                    child: Row(children: [
                      _TeamOrb(visual: itemVisual, size: 28),
                      const SizedBox(width: 9),
                      Expanded(child: Text(team.name, overflow: TextOverflow.ellipsis)),
                    ]),
                  );
                }).toList(),
              ),
            ),
          ),
          const SizedBox(width: 10),
          Text('${selected.members.length}', style: Theme.of(context).textTheme.labelMedium),
          if (widget.isOwner)
            IconButton(
              tooltip: 'Create Team',
              onPressed: _createTeam,
              icon: const Icon(Icons.add),
            ),
        ],
      ),
    );
  }
}

class _TeamOrb extends StatelessWidget {
  const _TeamOrb({required this.visual, required this.size});
  final TeamVisual visual;
  final double size;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [visual.primary, visual.secondary],
        ),
        boxShadow: [
          BoxShadow(color: visual.primary.withValues(alpha: .34), blurRadius: size * .55, spreadRadius: 1),
          BoxShadow(color: visual.secondary.withValues(alpha: .20), blurRadius: size * .8, spreadRadius: 2),
        ],
      ),
      child: Container(
        margin: EdgeInsets.all(size * .12),
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: Theme.of(context).colorScheme.surface.withValues(alpha: .22),
          border: Border.all(color: Colors.white.withValues(alpha: .28)),
        ),
        child: Icon(visual.icon, size: size * .42, color: Colors.white),
      ),
    );
  }
}

class _CreateTeamDialog extends StatefulWidget {
  const _CreateTeamDialog();

  @override
  State<_CreateTeamDialog> createState() => _CreateTeamDialogState();
}

class _CreateTeamDialogState extends State<_CreateTeamDialog> {
  late final TextEditingController _controller;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _submit() => Navigator.of(context).pop(_controller.text.trim());

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Create New Team'),
      content: TextField(
        controller: _controller,
        autofocus: true,
        decoration: const InputDecoration(labelText: 'Team name'),
        onSubmitted: (_) => _submit(),
      ),
      actions: <Widget>[
        TextButton(onPressed: () => Navigator.of(context).pop(), child: const Text('Cancel')),
        FilledButton(onPressed: _submit, child: const Text('Create')),
      ],
    );
  }
}
