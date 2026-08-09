import 'package:flutter/material.dart';

import '../../api/developer_access_api_client.dart';

class DeveloperAccessPage extends StatefulWidget {
  DeveloperAccessPage({DeveloperAccessApiClient? client, super.key})
      : client = client ?? DeveloperAccessApiClient();

  final DeveloperAccessApiClient client;

  @override
  State<DeveloperAccessPage> createState() => _DeveloperAccessPageState();
}

class _DeveloperAccessPageState extends State<DeveloperAccessPage> {
  bool _loading = true;
  bool _signedIn = false;
  String? _principal;
  String? _error;
  List<Map<String, dynamic>> _requests = const [];
  List<Map<String, dynamic>> _grants = const [];

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
      final session = await widget.client.getSession();
      final results = await Future.wait<Map<String, dynamic>>(<Future<Map<String, dynamic>>>[
        widget.client.getOwnerRequests(status: 'pending'),
        widget.client.getOwnerGrants(),
      ]);
      if (!mounted) return;
      setState(() {
        _signedIn = session['authenticated'] == true;
        _principal = session['principal']?.toString();
        _requests = _items(results[0]);
        _grants = _items(results[1]);
        _loading = false;
      });
    } on DeveloperAccessApiException catch (error) {
      if (!mounted) return;
      setState(() {
        _signedIn = false;
        _principal = null;
        _requests = const [];
        _grants = const [];
        _error = error.message;
        _loading = false;
      });
    }
  }

  static List<Map<String, dynamic>> _items(Map<String, dynamic> payload) {
    final raw = payload['items'];
    if (raw is! List) return const [];
    return raw.whereType<Map>().map((item) => Map<String, dynamic>.from(item)).toList();
  }

  List<String> _requestedScopes(Map<String, dynamic> request) {
    final raw = request['requested_scopes'];
    if (raw is! List) return const <String>['read'];
    return raw.map((value) => value.toString()).where((value) => value.isNotEmpty).toList();
  }

  Future<void> _approve(Map<String, dynamic> request, {required bool readOnly}) async {
    final requestId = request['request_id']?.toString() ?? '';
    if (requestId.isEmpty) return;
    final scopes = readOnly ? const <String>['read'] : _requestedScopes(request);
    try {
      await widget.client.approveRequest(
        requestId,
        scopes: scopes,
        expiresInSeconds: 3600,
      );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(readOnly ? 'อนุมัติ Read-only 1 ชั่วโมงแล้ว' : 'อนุมัติตาม Scope ที่ขอ 1 ชั่วโมงแล้ว')),
      );
      await _refresh();
    } on DeveloperAccessApiException catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(error.message)));
    }
  }

  Future<void> _reject(Map<String, dynamic> request) async {
    final requestId = request['request_id']?.toString() ?? '';
    if (requestId.isEmpty) return;
    try {
      await widget.client.rejectRequest(requestId, reason: 'Rejected by resource owner');
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('ปฏิเสธคำขอแล้ว')));
      await _refresh();
    } on DeveloperAccessApiException catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(error.message)));
    }
  }

  Future<void> _revoke(Map<String, dynamic> grant) async {
    final grantId = grant['grant_id']?.toString() ?? '';
    if (grantId.isEmpty) return;
    try {
      await widget.client.revokeGrant(grantId, reason: 'Revoked by resource owner');
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('เพิกถอนสิทธิ์แล้ว')));
      await _refresh();
    } on DeveloperAccessApiException catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(error.message)));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      key: const Key('developer-access-page'),
      appBar: AppBar(
        title: const Text('Developer Access'),
        actions: <Widget>[
          IconButton(
            key: const Key('developer-access-refresh'),
            tooltip: 'Refresh',
            onPressed: _loading ? null : _refresh,
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : !_signedIn
              ? _SignedOutState(error: _error, baseUrl: widget.client.baseUrl, onRetry: _refresh)
              : RefreshIndicator(
                  onRefresh: _refresh,
                  child: ListView(
                    padding: const EdgeInsets.all(20),
                    children: <Widget>[
                      _HeaderCard(principal: _principal ?? 'Authenticated owner'),
                      const SizedBox(height: 18),
                      Text('คำขอที่รออนุมัติ (${_requests.length})', style: Theme.of(context).textTheme.titleLarge),
                      const SizedBox(height: 10),
                      if (_requests.isEmpty)
                        const _EmptyCard(message: 'ไม่มีคำขอ Developer ที่รออนุมัติ')
                      else
                        ..._requests.map(
                          (request) => _RequestCard(
                            request: request,
                            onApprove: () => _approve(request, readOnly: false),
                            onApproveReadOnly: () => _approve(request, readOnly: true),
                            onReject: () => _reject(request),
                          ),
                        ),
                      const SizedBox(height: 22),
                      Text('สิทธิ์ที่กำลังใช้งาน (${_grants.length})', style: Theme.of(context).textTheme.titleLarge),
                      const SizedBox(height: 10),
                      if (_grants.isEmpty)
                        const _EmptyCard(message: 'ไม่มี Developer grant ที่ active')
                      else
                        ..._grants.map((grant) => _GrantCard(grant: grant, onRevoke: () => _revoke(grant))),
                    ],
                  ),
                ),
    );
  }
}

class _HeaderCard extends StatelessWidget {
  const _HeaderCard({required this.principal});
  final String principal;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            CircleAvatar(backgroundColor: scheme.primaryContainer, child: const Icon(Icons.admin_panel_settings_outlined)),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  const Text('Owner Approval Inbox', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
                  const SizedBox(height: 4),
                  Text(principal, key: const Key('developer-access-principal')),
                  const SizedBox(height: 8),
                  const Text('การอนุมัติเป็นสิทธิ์ overlay เท่านั้น เจ้าของไฟล์ยังคง ownership และการเข้าถึงไฟล์เดิมเหมือนเดิม'),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _RequestCard extends StatelessWidget {
  const _RequestCard({
    required this.request,
    required this.onApprove,
    required this.onApproveReadOnly,
    required this.onReject,
  });

  final Map<String, dynamic> request;
  final VoidCallback onApprove;
  final VoidCallback onApproveReadOnly;
  final VoidCallback onReject;

  @override
  Widget build(BuildContext context) {
    final scopes = (request['requested_scopes'] as List? ?? const []).join(', ');
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              children: <Widget>[
                Expanded(child: Text(request['resource_name']?.toString() ?? request['resource_id']?.toString() ?? 'Resource', style: const TextStyle(fontWeight: FontWeight.w800))),
                const Chip(label: Text('PENDING')),
              ],
            ),
            Text('Developer: ${request['developer_id'] ?? '-'}'),
            Text('Workspace: ${request['workspace_id'] ?? '-'}'),
            Text('Scope ที่ขอ: $scopes'),
            const SizedBox(height: 8),
            Text(request['purpose']?.toString() ?? ''),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: <Widget>[
                FilledButton.icon(onPressed: onApprove, icon: const Icon(Icons.check), label: const Text('อนุมัติ 1 ชม.')),
                OutlinedButton.icon(onPressed: onApproveReadOnly, icon: const Icon(Icons.visibility_outlined), label: const Text('Read-only 1 ชม.')),
                TextButton.icon(onPressed: onReject, icon: const Icon(Icons.close), label: const Text('ปฏิเสธ')),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _GrantCard extends StatelessWidget {
  const _GrantCard({required this.grant, required this.onRevoke});
  final Map<String, dynamic> grant;
  final VoidCallback onRevoke;

  @override
  Widget build(BuildContext context) {
    final scopes = (grant['scopes'] as List? ?? const []).join(', ');
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: ListTile(
        leading: const Icon(Icons.verified_user_outlined),
        title: Text(grant['resource_name']?.toString() ?? grant['resource_id']?.toString() ?? 'Resource'),
        subtitle: Text('Developer: ${grant['developer_id'] ?? '-'}\nScopes: $scopes\nOwner access unchanged: ${grant['owner_access_unchanged'] == true ? 'Yes' : 'Unknown'}'),
        isThreeLine: true,
        trailing: TextButton(onPressed: onRevoke, child: const Text('Revoke')),
      ),
    );
  }
}

class _EmptyCard extends StatelessWidget {
  const _EmptyCard({required this.message});
  final String message;

  @override
  Widget build(BuildContext context) => Card(
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Row(children: <Widget>[const Icon(Icons.inbox_outlined), const SizedBox(width: 10), Text(message)]),
        ),
      );
}

class _SignedOutState extends StatelessWidget {
  const _SignedOutState({required this.error, required this.baseUrl, required this.onRetry});
  final String? error;
  final String baseUrl;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 560),
        child: Card(
          margin: const EdgeInsets.all(24),
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: <Widget>[
                const Icon(Icons.lock_person_outlined, size: 48),
                const SizedBox(height: 12),
                const Text('ต้องลงชื่อเข้าใช้ในฐานะเจ้าของไฟล์', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
                const SizedBox(height: 8),
                const Text('Research OS จะไม่รับ Developer ID จาก client โดยตรง การยืนยันตัวตนต้องผ่าน trusted identity gateway ของ Developer Platform'),
                const SizedBox(height: 8),
                SelectableText(baseUrl, style: Theme.of(context).textTheme.bodySmall),
                if (error != null) ...<Widget>[const SizedBox(height: 10), Text(error!, style: TextStyle(color: Theme.of(context).colorScheme.error))],
                const SizedBox(height: 16),
                FilledButton.icon(onPressed: onRetry, icon: const Icon(Icons.refresh), label: const Text('ตรวจสถานะอีกครั้ง')),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
