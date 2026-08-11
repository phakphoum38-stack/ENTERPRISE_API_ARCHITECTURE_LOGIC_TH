import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class CheckInPage extends StatefulWidget {
  const CheckInPage({super.key});

  @override
  State<CheckInPage> createState() => _CheckInPageState();
}

class _CheckInPageState extends State<CheckInPage> {
  static const _storageKey = 'research_os_checkin_records_v1';

  final TextEditingController _noteController = TextEditingController();
  List<Map<String, dynamic>> _records = <Map<String, dynamic>>[];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _noteController.dispose();
    super.dispose();
  }

  Map<String, dynamic>? get _activeRecord {
    for (final record in _records) {
      final checkOut = (record['check_out'] ?? '').toString();
      if (checkOut.isEmpty) return record;
    }
    return null;
  }

  Future<void> _load() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_storageKey);
    final records = <Map<String, dynamic>>[];
    if (raw != null && raw.trim().isNotEmpty) {
      try {
        final decoded = jsonDecode(raw);
        if (decoded is List) {
          records.addAll(
            decoded
                .whereType<Map>()
                .map((item) => Map<String, dynamic>.from(item)),
          );
        }
      } on Object {
        // Keep the page usable if an older local value is malformed.
      }
    }
    if (!mounted) return;
    setState(() {
      _records = records;
      _loading = false;
    });
  }

  Future<void> _save() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_storageKey, jsonEncode(_records));
  }

  Future<void> _checkIn() async {
    if (_activeRecord != null) return;
    final now = DateTime.now();
    setState(() {
      _records.insert(0, <String, dynamic>{
        'id': 'checkin-${now.microsecondsSinceEpoch.toRadixString(36)}',
        'check_in': now.toIso8601String(),
        'check_out': '',
        'note': _noteController.text.trim(),
      });
      _noteController.clear();
    });
    await _save();
  }

  Future<void> _checkOut() async {
    final active = _activeRecord;
    if (active == null) return;
    final now = DateTime.now();
    setState(() {
      active['check_out'] = now.toIso8601String();
      final currentNote = (active['note'] ?? '').toString().trim();
      final extraNote = _noteController.text.trim();
      if (extraNote.isNotEmpty) {
        active['note'] = currentNote.isEmpty
            ? extraNote
            : '$currentNote • $extraNote';
      }
      _noteController.clear();
    });
    await _save();
  }

  DateTime? _dateFrom(Object? value) =>
      DateTime.tryParse((value ?? '').toString())?.toLocal();

  String _two(int value) => value.toString().padLeft(2, '0');

  String _date(DateTime value) =>
      '${_two(value.day)}/${_two(value.month)}/${value.year}';

  String _time(DateTime value) =>
      '${_two(value.hour)}:${_two(value.minute)}';

  String _duration(Map<String, dynamic> record) {
    final start = _dateFrom(record['check_in']);
    if (start == null) return '-';
    final end = _dateFrom(record['check_out']) ?? DateTime.now();
    final minutes = end.difference(start).inMinutes.clamp(0, 1000000000);
    final hours = minutes ~/ 60;
    final remain = minutes % 60;
    return '${hours}ชม. ${remain}น.';
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Center(child: CircularProgressIndicator());
    }

    final active = _activeRecord;
    final now = DateTime.now();
    final scheme = Theme.of(context).colorScheme;

    return LayoutBuilder(
      builder: (context, constraints) {
        final compact = constraints.maxWidth < 760;
        return ListView(
          key: const Key('checkin-page'),
          padding: EdgeInsets.all(compact ? 16 : 28),
          children: <Widget>[
            Wrap(
              alignment: WrapAlignment.spaceBetween,
              crossAxisAlignment: WrapCrossAlignment.center,
              spacing: 16,
              runSpacing: 10,
              children: <Widget>[
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      'Check-in',
                      style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                            fontWeight: FontWeight.w800,
                          ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'บันทึกเวลาแบบ Local-first • ข้อมูลอยู่ในเครื่องนี้',
                      style: TextStyle(color: scheme.onSurfaceVariant),
                    ),
                  ],
                ),
                Semantics(
                  label: 'เวลาปัจจุบัน',
                  child: Text(
                    '${_date(now)}  ${_time(now)}',
                    key: const Key('checkin-current-time'),
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.w700,
                        ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),
            Card(
              key: const Key('checkin-status-card'),
              child: Padding(
                padding: EdgeInsets.all(compact ? 18 : 24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: <Widget>[
                    Row(
                      children: <Widget>[
                        CircleAvatar(
                          backgroundColor: active == null
                              ? scheme.surfaceContainerHighest
                              : scheme.primaryContainer,
                          child: Icon(
                            active == null
                                ? Icons.login_rounded
                                : Icons.work_history_outlined,
                            color: active == null
                                ? scheme.onSurfaceVariant
                                : scheme.onPrimaryContainer,
                          ),
                        ),
                        const SizedBox(width: 14),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: <Widget>[
                              Text(
                                active == null
                                    ? 'พร้อมเช็คอิน'
                                    : 'กำลังเช็คอิน',
                                key: const Key('checkin-status-text'),
                                style: Theme.of(context)
                                    .textTheme
                                    .titleLarge
                                    ?.copyWith(fontWeight: FontWeight.w800),
                              ),
                              if (active != null) ...<Widget>[
                                const SizedBox(height: 3),
                                Text(
                                  'เริ่ม ${_time(_dateFrom(active['check_in'])!)} • ${_duration(active)}',
                                ),
                              ],
                            ],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 20),
                    TextField(
                      key: const Key('checkin-note'),
                      controller: _noteController,
                      maxLines: 2,
                      decoration: InputDecoration(
                        labelText: active == null
                            ? 'หมายเหตุก่อนเช็คอิน (ไม่บังคับ)'
                            : 'หมายเหตุก่อนเช็คเอาต์ (ไม่บังคับ)',
                        border: const OutlineInputBorder(),
                        prefixIcon: const Icon(Icons.notes_outlined),
                      ),
                    ),
                    const SizedBox(height: 14),
                    if (compact)
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: _actionButtons(active),
                      )
                    else
                      Row(children: _actionButtons(active)),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),
            Text(
              'ประวัติล่าสุด',
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.w800,
                  ),
            ),
            const SizedBox(height: 10),
            if (_records.isEmpty)
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(28),
                  child: Center(
                    child: Text(
                      'ยังไม่มีประวัติ Check-in',
                      style: TextStyle(color: scheme.onSurfaceVariant),
                    ),
                  ),
                ),
              )
            else
              ..._records.take(14).map(_historyCard),
          ],
        );
      },
    );
  }

  List<Widget> _actionButtons(Map<String, dynamic>? active) {
    final checkInButton = FilledButton.icon(
      key: const Key('checkin-button'),
      onPressed: active == null ? _checkIn : null,
      icon: const Icon(Icons.login_rounded),
      label: const Text('เช็คอิน'),
    );
    final checkOutButton = OutlinedButton.icon(
      key: const Key('checkout-button'),
      onPressed: active == null ? null : _checkOut,
      icon: const Icon(Icons.logout_rounded),
      label: const Text('เช็คเอาต์'),
    );
    return <Widget>[
      Expanded(child: checkInButton),
      const SizedBox(width: 12, height: 12),
      Expanded(child: checkOutButton),
    ];
  }

  Widget _historyCard(Map<String, dynamic> record) {
    final start = _dateFrom(record['check_in']);
    final end = _dateFrom(record['check_out']);
    final note = (record['note'] ?? '').toString().trim();
    if (start == null) return const SizedBox.shrink();

    return Card(
      key: Key('checkin-record-${record['id']}'),
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        leading: Icon(
          end == null ? Icons.timelapse_rounded : Icons.check_circle_outline,
        ),
        title: Text(
          '${_date(start)} • ${_time(start)} - ${end == null ? 'กำลังทำงาน' : _time(end)}',
          style: const TextStyle(fontWeight: FontWeight.w700),
        ),
        subtitle: Text(
          note.isEmpty ? 'ระยะเวลา ${_duration(record)}' : 'ระยะเวลา ${_duration(record)} • $note',
        ),
        trailing: Text(end == null ? 'ACTIVE' : 'DONE'),
      ),
    );
  }
}
