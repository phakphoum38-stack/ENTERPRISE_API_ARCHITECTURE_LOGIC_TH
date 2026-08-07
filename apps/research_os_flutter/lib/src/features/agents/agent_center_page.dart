import 'package:flutter/material.dart';

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
    return Scaffold(
      appBar: AppBar(title: const Text('Agent Center')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: <Widget>[
          Text('Research OS Agent Platform', style: Theme.of(context).textTheme.headlineMedium),
          const SizedBox(height: 8),
          const Text('ศูนย์กลางผู้ช่วยเฉพาะทาง พร้อม Agent Runtime สำหรับ routing, queue, events, shared context และ confirmation gate'),
          const SizedBox(height: 16),
          const Card(
            child: ListTile(
              leading: Icon(Icons.route_outlined),
              title: Text('Capability Router + Agent Runtime'),
              subtitle: Text('รับ objective → เลือก Agent → เข้า Task Queue → Event Bus → Execute และบังคับยืนยันก่อนงานที่มีสิทธิ์เขียน'),
              trailing: Chip(label: Text('Runtime 1.0')),
            ),
          ),
          const SizedBox(height: 12),
          const Wrap(
            spacing: 8,
            runSpacing: 8,
            children: <Widget>[
              Chip(avatar: Icon(Icons.queue_outlined, size: 18), label: Text('Task Queue: Active')),
              Chip(avatar: Icon(Icons.swap_horiz, size: 18), label: Text('Event Bus: Active')),
              Chip(avatar: Icon(Icons.memory_outlined, size: 18), label: Text('Shared Context: Local')),
              Chip(avatar: Icon(Icons.verified_user_outlined, size: 18), label: Text('Confirmation Gate')),
            ],
          ),
          const SizedBox(height: 16),
          LayoutBuilder(
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
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: <Widget>[
                          Row(children: <Widget>[
                            Icon(agent.icon, size: 30),
                            const SizedBox(width: 10),
                            Expanded(child: Text(agent.name, style: Theme.of(context).textTheme.titleMedium)),
                            const Chip(label: Text('Registered')),
                          ]),
                          const SizedBox(height: 12),
                          Text(agent.capabilities),
                          const SizedBox(height: 10),
                          Text('Permissions: ${agent.permissions}', style: Theme.of(context).textTheme.bodySmall),
                        ],
                      ),
                    ),
                  ),
                )).toList(),
              );
            },
          ),
          const SizedBox(height: 20),
          const Card(
            child: ListTile(
              leading: Icon(Icons.verified_user_outlined),
              title: Text('Write actions require confirmation'),
              subtitle: Text('Agent ที่แก้ Calendar/Google Workspace หรือข้อมูลภายนอกจะหยุดที่ awaiting_confirmation จนกว่าผู้ใช้จะยืนยัน'),
            ),
          ),
          const Card(
            child: ListTile(
              leading: Icon(Icons.memory_outlined),
              title: Text('Shared Context แบบ Local-first'),
              subtitle: Text('Context ของ Agent ถูกเตรียมให้เก็บใต้ ResearchOSData/agents เพื่อใช้ต่อเนื่องโดยไม่ต้องพึ่ง Cloud'),
            ),
          ),
          const Card(
            child: ListTile(
              leading: Icon(Icons.construction_outlined),
              title: Text('Domain Executors เป็นลำดับถัดไป'),
              subtitle: Text('Runtime dispatch ทำงานแล้ว ขั้นถัดไปคือผูก executor จริงของ Research, GitHub, Google Workspace, Document และ Shift Agent เข้ากับ Task Queue'),
            ),
          ),
        ],
      ),
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
