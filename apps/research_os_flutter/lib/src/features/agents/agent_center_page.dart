import 'package:flutter/material.dart';

import '../../ui/enterprise_components.dart';

class AgentCenterPage extends StatelessWidget {
  const AgentCenterPage({super.key});

  static const _agents = <_AgentView>[
    _AgentView('Research Agent', Icons.psychology_outlined, 'Research • Synthesis • Memory • Knowledge', 'memory.read • knowledge.read/write'),
    _AgentView('Document Agent', Icons.description_outlined, 'PDF • Word • Excel • PowerPoint • Markdown', 'documents.read • knowledge.write'),
    _AgentView('GitHub Agent', Icons.account_tree_outlined, 'Repository • Commit • PR • Issues • Workflows', 'github.read'),
    _AgentView('Google Workspace Agent', Icons.apps_outlined, 'Drive • Docs • Sheets • Calendar • Gmail • Workspace', 'google.read • write with confirmation'),
    _AgentView('Shift Agent', Icons.calendar_view_week_outlined, 'Roster • Replacement • Leave • Conflict • Calendar Sync', 'sheets.read • calendar write with confirmation'),
  ];

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(24, 22, 24, 32),
      children: <Widget>[
        const EnterprisePageHeader(
          icon: Icons.smart_toy_outlined,
          title: 'Agent Center',
          subtitle: 'จัดการผู้ช่วยเฉพาะทาง, routing, task queue, events และสิทธิ์การทำงานจากศูนย์กลางเดียว',
        ),
        const SizedBox(height: 24),
        const EnterpriseSection(
          title: 'Runtime overview',
          subtitle: 'สถานะของ Agent Runtime 1.0',
          child: Wrap(
            spacing: 12,
            runSpacing: 12,
            children: <Widget>[
              SizedBox(width: 230, child: EnterpriseStatusTile(icon: Icons.route_outlined, title: 'Router', value: 'Capability based', caption: 'Research fallback')),
              SizedBox(width: 230, child: EnterpriseStatusTile(icon: Icons.queue_outlined, title: 'Task Queue', value: 'Active', caption: 'Local runtime')),
              SizedBox(width: 230, child: EnterpriseStatusTile(icon: Icons.swap_horiz, title: 'Event Bus', value: 'Active', caption: 'Runtime events')),
              SizedBox(width: 230, child: EnterpriseStatusTile(icon: Icons.memory_outlined, title: 'Shared Context', value: 'Local-first', caption: 'ResearchOSData/agents')),
            ],
          ),
        ),
        const SizedBox(height: 28),
        EnterpriseSection(
          title: 'Registered agents',
          subtitle: 'Agent ทุกตัวใช้ permission model และ confirmation policy ชุดเดียวกัน',
          child: LayoutBuilder(
            builder: (context, constraints) {
              final columns = constraints.maxWidth >= 1050 ? 3 : constraints.maxWidth >= 650 ? 2 : 1;
              final width = (constraints.maxWidth - (columns - 1) * 12) / columns;
              return Wrap(
                spacing: 12,
                runSpacing: 12,
                children: _agents.map((agent) => SizedBox(
                  width: width,
                  child: Card(
                    child: Padding(
                      padding: const EdgeInsets.all(18),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: <Widget>[
                          Row(children: <Widget>[
                            Container(
                              width: 40,
                              height: 40,
                              alignment: Alignment.center,
                              decoration: BoxDecoration(
                                color: Theme.of(context).colorScheme.secondaryContainer,
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: Icon(agent.icon),
                            ),
                            const SizedBox(width: 12),
                            Expanded(child: Text(agent.name, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700))),
                            const Chip(label: Text('Ready')),
                          ]),
                          const SizedBox(height: 14),
                          Text(agent.capabilities),
                          const SizedBox(height: 12),
                          const Divider(height: 1),
                          const SizedBox(height: 10),
                          Text('Permissions', style: Theme.of(context).textTheme.labelMedium),
                          const SizedBox(height: 3),
                          Text(agent.permissions, style: Theme.of(context).textTheme.bodySmall),
                        ],
                      ),
                    ),
                  ),
                )).toList(),
              );
            },
          ),
        ),
        const SizedBox(height: 28),
        const EnterpriseSection(
          title: 'Governance',
          subtitle: 'กติกากลางสำหรับ Agent ทุกตัว',
          child: Column(
            children: <Widget>[
              Card(child: ListTile(leading: Icon(Icons.verified_user_outlined), title: Text('Write actions require confirmation'), subtitle: Text('งานที่แก้ Calendar, Google Workspace หรือข้อมูลภายนอกจะหยุดรอการยืนยันก่อน Execute'))),
              SizedBox(height: 8),
              Card(child: ListTile(leading: Icon(Icons.storage_outlined), title: Text('Shared Context แบบ Local-first'), subtitle: Text('Context ของ Agent อยู่ใต้ ResearchOSData/agents และไม่บังคับพึ่ง Cloud'))),
              SizedBox(height: 8),
              Card(child: ListTile(leading: Icon(Icons.construction_outlined), title: Text('Domain Executors'), subtitle: Text('ขั้นต่อไปคือผูก executor จริงของ Research, GitHub, Google Workspace, Document และ Shift เข้ากับ Runtime'))),
            ],
          ),
        ),
      ],
    );
  }
}

class _AgentView {
  const _AgentView(this.name, this.icon, this.capabilities, this.permissions);
  final String name;
  final IconData icon;
  final String capabilities;
  final String permissions;
}
