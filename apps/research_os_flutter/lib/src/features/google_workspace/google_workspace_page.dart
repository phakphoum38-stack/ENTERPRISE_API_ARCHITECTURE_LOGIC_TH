import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../api/research_os_api_client.dart';

class GoogleWorkspacePage extends StatefulWidget {
  const GoogleWorkspacePage({required this.apiClient, super.key});

  final ResearchOSApiClient apiClient;

  @override
  State<GoogleWorkspacePage> createState() => _GoogleWorkspacePageState();
}

class _GoogleWorkspacePageState extends State<GoogleWorkspacePage> {
  bool _loading = true;
  bool _working = false;
  String? _error;
  Map<String, dynamic> _dashboard = const <String, dynamic>{};

  @override
  void initState() {
    super.initState();
    _refresh();
  }

  Future<void> _refresh() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final payload = await widget.apiClient.getGoogleWorkspaceDashboard();
      if (!mounted) return;
      setState(() {
        _dashboard = payload;
        _loading = false;
      });
    } on Object catch (error) {
      if (!mounted) return;
      setState(() {
        _error = error.toString();
        _loading = false;
      });
    }
  }

  Future<void> _connect() async {
    if (_working) return;
    setState(() {
      _working = true;
      _error = null;
    });
    try {
      final payload = await widget.apiClient.startGoogleWorkspaceOAuth();
      final rawUrl = payload['authorization_url']?.toString() ?? '';
      final uri = Uri.tryParse(rawUrl);
      if (uri == null || !uri.hasScheme) {
        throw const ResearchOSApiException(
            'Backend did not return a valid Google authorization URL.');
      }
      final launched =
          await launchUrl(uri, mode: LaunchMode.externalApplication);
      if (!launched) {
        throw const ResearchOSApiException(
            'ไม่สามารถเปิดหน้าล็อกอิน Google ได้');
      }
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
            content: Text(
                'เปิด Google แล้ว เมื่อล็อกอินเสร็จให้กลับมาหน้านี้และกดรีเฟรช')),
      );
    } on Object catch (error) {
      if (mounted) setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _working = false);
    }
  }

  Future<void> _disconnect() async {
    if (_working) return;
    setState(() {
      _working = true;
      _error = null;
    });
    try {
      await widget.apiClient.disconnectGoogleWorkspace();
      await _refresh();
    } on Object catch (error) {
      if (mounted) setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _working = false);
    }
  }

  Future<void> _setService(String service, bool enabled) async {
    final raw = _dashboard['services'];
    if (raw is! List) return;
    final enabledServices = raw
        .whereType<Map>()
        .where((item) => item['enabled'] == true)
        .map((item) => item['service'].toString())
        .toSet();
    if (enabled) {
      enabledServices.add(service);
    } else {
      enabledServices.remove(service);
    }
    setState(() => _working = true);
    try {
      final payload = await widget.apiClient
          .setGoogleWorkspaceServices(enabledServices.toList()..sort());
      if (!mounted) return;
      setState(() => _dashboard = payload);
    } on Object catch (error) {
      if (mounted) setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _working = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final connected = _dashboard['connected'] == true;
    final oauthConfigured = _dashboard['oauth_configured'] == true;
    final services = _dashboard['services'] is List
        ? List<dynamic>.from(_dashboard['services'] as List)
        : const <dynamic>[];
    final enabledCount =
        services.where((item) => item is Map && item['enabled'] == true).length;

    return ListView(
      padding: const EdgeInsets.fromLTRB(24, 24, 24, 40),
      children: <Widget>[
        _Heading(
          icon: Icons.apps_outlined,
          title: 'Google Workspace Hub',
          subtitle:
              'เชื่อมบริการ Google ผ่าน OAuth โดยเก็บ Client Secret และ Token ไว้ฝั่ง Backend เท่านั้น',
          action: IconButton(
            tooltip: 'รีเฟรชสถานะ',
            onPressed: _loading || _working ? null : _refresh,
            icon: const Icon(Icons.refresh),
          ),
        ),
        const SizedBox(height: 20),
        if (_loading) const LinearProgressIndicator(),
        if (_error != null)
          Card(
            child: ListTile(
              leading: const Icon(Icons.error_outline),
              title: const Text('Google Workspace'),
              subtitle: Text(_error!),
              trailing: IconButton(
                  onPressed: _refresh, icon: const Icon(Icons.refresh)),
            ),
          ),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(18),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Row(
                  children: <Widget>[
                    Icon(
                        connected
                            ? Icons.cloud_done_outlined
                            : Icons.cloud_off_outlined,
                        size: 32),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: <Widget>[
                          Text(
                            connected
                                ? 'Google account connected'
                                : 'Google account not connected',
                            style: Theme.of(context).textTheme.titleLarge,
                          ),
                          const SizedBox(height: 4),
                          Text(
                            oauthConfigured
                                ? 'OAuth credentials พร้อมใช้งานบน Research OS Backend'
                                : 'ตั้ง Google OAuth Client ID และ Client Secret ที่ Local API ก่อน',
                          ),
                        ],
                      ),
                    ),
                    Chip(
                        label: Text(connected
                            ? 'Connected'
                            : oauthConfigured
                                ? 'Ready'
                                : 'Not configured')),
                  ],
                ),
                const SizedBox(height: 16),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: <Widget>[
                    FilledButton.icon(
                      key: const Key('google-workspace-connect'),
                      onPressed: _working || connected || !oauthConfigured
                          ? null
                          : _connect,
                      icon: const Icon(Icons.login),
                      label: const Text('เชื่อมบัญชี Google'),
                    ),
                    OutlinedButton.icon(
                      onPressed: _working ? null : _refresh,
                      icon: const Icon(Icons.sync),
                      label: const Text('ตรวจสถานะ'),
                    ),
                    if (connected)
                      OutlinedButton.icon(
                        onPressed: _working ? null : _disconnect,
                        icon: const Icon(Icons.link_off),
                        label: const Text('ยกเลิกการเชื่อมต่อ'),
                      ),
                  ],
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 24),
        Row(
          children: <Widget>[
            Expanded(
                child: Text('Workspace services',
                    style: Theme.of(context).textTheme.titleLarge)),
            Chip(label: Text('$enabledCount/${services.length} enabled')),
          ],
        ),
        const SizedBox(height: 6),
        const Text(
            'เปิดเฉพาะบริการที่ต้องใช้ เพื่อลด OAuth scopes ที่ไม่จำเป็น'),
        const SizedBox(height: 12),
        LayoutBuilder(
          builder: (context, constraints) {
            final columns = constraints.maxWidth >= 1000
                ? 3
                : constraints.maxWidth >= 620
                    ? 2
                    : 1;
            final width = (constraints.maxWidth - (columns - 1) * 12) / columns;
            return Wrap(
              spacing: 12,
              runSpacing: 12,
              children: services.map((raw) {
                final item = raw is Map
                    ? Map<String, dynamic>.from(raw)
                    : const <String, dynamic>{};
                final service = item['service']?.toString() ?? 'unknown';
                final enabled = item['enabled'] == true;
                final state = item['state']?.toString() ?? 'unknown';
                return SizedBox(
                  width: width,
                  child: Card(
                    child: SwitchListTile(
                      value: enabled,
                      onChanged: _working
                          ? null
                          : (value) => _setService(service, value),
                      secondary: Icon(_iconFor(service)),
                      title: Text(_titleFor(service)),
                      subtitle: Text('$state • ${_descriptionFor(service)}'),
                    ),
                  ),
                );
              }).toList(),
            );
          },
        ),
        const SizedBox(height: 24),
        const Card(
          child: ListTile(
            leading: Icon(Icons.security_outlined),
            title: Text('Backend-only credentials'),
            subtitle: Text(
                'Flutter ไม่ได้รับ Google Client Secret, access token หรือ refresh token และ OAuth callback กลับเข้า Local API โดยตรง'),
            trailing: Chip(label: Text('Local-first')),
          ),
        ),
      ],
    );
  }

  static String _titleFor(String value) => switch (value) {
        'drive' => 'Drive',
        'docs' => 'Docs',
        'sheets' => 'Sheets',
        'calendar' => 'Calendar',
        'gmail' => 'Gmail',
        'contacts' => 'Contacts',
        'tasks' => 'Tasks',
        'keep' => 'Keep',
        'meet' => 'Meet',
        'forms' => 'Forms',
        'chat' => 'Google Chat',
        _ => value,
      };

  static String _descriptionFor(String value) => switch (value) {
        'drive' => 'ไฟล์ โฟลเดอร์ Backup และ Sync',
        'docs' => 'อ่านและสรุปเอกสาร',
        'sheets' => 'ตาราง เวร และวิเคราะห์ข้อมูล',
        'calendar' => 'ปฏิทิน นัดหมาย และเวร',
        'gmail' => 'ค้นหา สรุป และจัดการอีเมล',
        'contacts' => 'รายชื่อและข้อมูลผู้ติดต่อ',
        'tasks' => 'งานและ To-do',
        'keep' => 'โน้ตและความรู้สั้น',
        'meet' => 'พื้นที่ประชุม Meet',
        'forms' => 'แบบฟอร์มและคำตอบ',
        'chat' => 'Spaces และข้อความ',
        _ => '',
      };

  static IconData _iconFor(String value) => switch (value) {
        'drive' => Icons.cloud_outlined,
        'docs' => Icons.description_outlined,
        'sheets' => Icons.table_chart_outlined,
        'calendar' => Icons.calendar_month_outlined,
        'gmail' => Icons.mail_outline,
        'contacts' => Icons.contacts_outlined,
        'tasks' => Icons.task_alt_outlined,
        'keep' => Icons.lightbulb_outline,
        'meet' => Icons.video_call_outlined,
        'forms' => Icons.list_alt_outlined,
        'chat' => Icons.forum_outlined,
        _ => Icons.extension_outlined,
      };
}

class _Heading extends StatelessWidget {
  const _Heading(
      {required this.icon,
      required this.title,
      required this.subtitle,
      required this.action});
  final IconData icon;
  final String title;
  final String subtitle;
  final Widget action;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Container(
          width: 46,
          height: 46,
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: Theme.of(context).colorScheme.primaryContainer,
            borderRadius: BorderRadius.circular(14),
          ),
          child: Icon(icon),
        ),
        const SizedBox(width: 14),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text(title, style: Theme.of(context).textTheme.headlineSmall),
              const SizedBox(height: 4),
              Text(subtitle, style: Theme.of(context).textTheme.bodyMedium),
            ],
          ),
        ),
        action,
      ],
    );
  }
}
