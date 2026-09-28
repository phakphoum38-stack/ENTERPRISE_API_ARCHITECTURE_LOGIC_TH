import 'dart:io';

import 'package:flutter/material.dart';

import 'owner_api.dart';

class OwnerFriendAppV3 extends StatefulWidget {
  const OwnerFriendAppV3({
    required this.api,
    this.startup,
    this.startupError,
    super.key,
  });

  final OwnerFriendApi api;
  final Map<String, dynamic>? startup;
  final String? startupError;

  @override
  State<OwnerFriendAppV3> createState() => _OwnerFriendAppV3State();
}

class _OwnerFriendAppV3State extends State<OwnerFriendAppV3> {
  int _index = 0;
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    final connected = widget.startupError == null;

    const sections = <String>[
      'Chat',
      'Capabilities',
      'Memory',
      'Provider',
    ];

    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Research OS Friend',
      theme: ThemeData(
        useMaterial3: true,
        colorSchemeSeed: const Color(0xFF6558D9),
        scaffoldBackgroundColor: const Color(0xFFF8F8FB),
        inputDecorationTheme: const InputDecorationTheme(
          border: OutlineInputBorder(),
        ),
      ),
      home: Scaffold(
        body: SafeArea(
          child: Row(
            children: <Widget>[
              _SideBar(
                selectedIndex: _index,
                expanded: _expanded,
                connected: connected,
                onToggle: () {
                  setState(() => _expanded = !_expanded);
                },
                onSelected: (value) {
                  setState(() => _index = value);
                },
              ),
              const VerticalDivider(width: 1),
              Expanded(
                child: Column(
                  children: <Widget>[
                    _TopBar(
                      title: sections[_index],
                      connected: connected,
                    ),
                    const Divider(height: 1),
                    Expanded(
                      child: IndexedStack(
                        index: _index,
                        children: <Widget>[
                          _FriendChat(api: widget.api),
                          _Capabilities(
                            api: widget.api,
                            startup: widget.startup,
                          ),
                          _Memory(api: widget.api),
                          _Provider(api: widget.api),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _SideBar extends StatelessWidget {
  const _SideBar({
    required this.selectedIndex,
    required this.expanded,
    required this.connected,
    required this.onToggle,
    required this.onSelected,
  });

  final int selectedIndex;
  final bool expanded;
  final bool connected;
  final VoidCallback onToggle;
  final ValueChanged<int> onSelected;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return AnimatedContainer(
      duration: const Duration(milliseconds: 180),
      width: expanded ? 220 : 78,
      color: colorScheme.surface,
      child: Column(
        children: <Widget>[
          const SizedBox(height: 8),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 10),
            child: Row(
              children: <Widget>[
                IconButton(
                  tooltip: expanded ? 'ย่อเมนู' : 'ขยายเมนู',
                  onPressed: onToggle,
                  icon: const Icon(Icons.menu),
                ),
                if (expanded) ...<Widget>[
                  const SizedBox(width: 6),
                  const Expanded(
                    child: Text(
                      'Research OS',
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                ],
              ],
            ),
          ),
          const SizedBox(height: 8),
          Expanded(
            child: NavigationRail(
              selectedIndex: selectedIndex,
              extended: expanded,
              groupAlignment: -0.9,
              labelType: expanded
                  ? NavigationRailLabelType.none
                  : NavigationRailLabelType.all,
              onDestinationSelected: onSelected,
              destinations: const <NavigationRailDestination>[
                NavigationRailDestination(
                  icon: Icon(Icons.chat_bubble_outline),
                  selectedIcon: Icon(Icons.chat_bubble),
                  label: Text('Friend'),
                ),
                NavigationRailDestination(
                  icon: Icon(Icons.auto_awesome_outlined),
                  selectedIcon: Icon(Icons.auto_awesome),
                  label: Text('Capabilities'),
                ),
                NavigationRailDestination(
                  icon: Icon(Icons.memory_outlined),
                  selectedIcon: Icon(Icons.memory),
                  label: Text('Memory'),
                ),
                NavigationRailDestination(
                  icon: Icon(Icons.tune_outlined),
                  selectedIcon: Icon(Icons.tune),
                  label: Text('Provider'),
                ),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              mainAxisAlignment: expanded
                  ? MainAxisAlignment.start
                  : MainAxisAlignment.center,
              children: <Widget>[
                Icon(
                  connected
                      ? Icons.check_circle
                      : Icons.error_outline,
                  size: 18,
                  color: connected
                      ? Colors.green
                      : colorScheme.error,
                ),
                if (expanded) ...<Widget>[
                  const SizedBox(width: 8),
                  Text(
                    connected
                        ? 'Service online'
                        : 'Service offline',
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _TopBar extends StatelessWidget {
  const _TopBar({
    required this.title,
    required this.connected,
  });

  final String title;
  final bool connected;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return SizedBox(
      height: 64,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 22),
        child: Row(
          children: <Widget>[
            Text(
              title,
              style: Theme.of(context)
                  .textTheme
                  .titleLarge
                  ?.copyWith(fontWeight: FontWeight.w700),
            ),
            const Spacer(),
            Container(
              padding: const EdgeInsets.symmetric(
                horizontal: 12,
                vertical: 7,
              ),
              decoration: BoxDecoration(
                color: colorScheme.surfaceContainerHighest,
                borderRadius: BorderRadius.circular(999),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: <Widget>[
                  Icon(
                    connected ? Icons.link : Icons.link_off,
                    size: 16,
                  ),
                  const SizedBox(width: 6),
                  Text(
                    connected
                        ? 'Friend Service connected'
                        : 'Friend Service offline',
                  ),
                ],
              ),
            ),
            const SizedBox(width: 10),
            const Chip(
              label: Text('UI V3'),
            ),
          ],
        ),
      ),
    );
  }
}

enum _ChatMode {
  normal,
  files,
  library,
  image,
  web,
  deepResearch,
  calendar,
}

extension _ChatModeUi on _ChatMode {
  String get title => switch (this) {
        _ChatMode.normal => 'Normal',
        _ChatMode.files => 'เพิ่มรูปภาพและไฟล์',
        _ChatMode.library => 'เพิ่มจากคลัง',
        _ChatMode.image => 'สร้างรูปภาพ',
        _ChatMode.web => 'ค้นหาเว็บ',
        _ChatMode.deepResearch => 'หาข้อมูลเชิงลึก',
        _ChatMode.calendar => 'Google Calendar',
      };

  String get subtitle => switch (this) {
        _ChatMode.normal => 'คุย วิเคราะห์ และวางแผน',
        _ChatMode.files =>
          'เลือกไฟล์จากเครื่องและส่งบริบทให้ Friend',
        _ChatMode.library =>
          'เลือกโฟลเดอร์คลังความรู้จากเครื่อง',
        _ChatMode.image =>
          'เตรียมคำสั่งสร้างภาพสำหรับ Provider',
        _ChatMode.web =>
          'เปิดผลค้นหาเว็บจริงในเบราว์เซอร์พร้อมส่งคำถามให้ Friend',
        _ChatMode.deepResearch =>
          'เพิ่มความซับซ้อน การวิเคราะห์ และการตรวจคุณภาพ',
        _ChatMode.calendar =>
          'เปิด Google Calendar และทำงานต่อกับ Friend',
      };

  IconData get icon => switch (this) {
        _ChatMode.normal => Icons.chat_bubble_outline,
        _ChatMode.files => Icons.attach_file,
        _ChatMode.library => Icons.library_books_outlined,
        _ChatMode.image => Icons.image_outlined,
        _ChatMode.web => Icons.language,
        _ChatMode.deepResearch => Icons.travel_explore,
        _ChatMode.calendar => Icons.calendar_month_outlined,
      };

  List<String> get skills => switch (this) {
        _ChatMode.normal => const <String>[
            'analysis',
            'planning',
            'memory',
            'quality',
          ],
        _ChatMode.files => const <String>[
            'documents',
            'analysis',
            'memory',
            'quality',
          ],
        _ChatMode.library => const <String>[
            'memory',
            'documents',
            'analysis',
            'quality',
          ],
        _ChatMode.image => const <String>[
            'planning',
            'documents',
            'quality',
          ],
        _ChatMode.web => const <String>[
            'research',
            'analysis',
            'quality',
          ],
        _ChatMode.deepResearch => const <String>[
            'research',
            'analysis',
            'planning',
            'memory',
            'quality',
          ],
        _ChatMode.calendar => const <String>[
            'automation',
            'planning',
            'memory',
            'quality',
          ],
      };
}

class _Attachment {
  const _Attachment({
    required this.path,
    required this.label,
    required this.context,
  });

  final String path;
  final String label;
  final String context;
}

class _ChatTurn {
  const _ChatTurn({
    required this.user,
    required this.answer,
    required this.provider,
  });

  final String user;
  final String answer;
  final String provider;
}

class _FriendChat extends StatefulWidget {
  const _FriendChat({
    required this.api,
  });

  final OwnerFriendApi api;

  @override
  State<_FriendChat> createState() => _FriendChatState();
}

class _FriendChatState extends State<_FriendChat> {
  static const int _maxTextFileBytes = 128 * 1024;
  static const int _maxAttachmentContextChars = 220000;

  static const Set<String> _textExtensions = <String>{
    'txt',
    'md',
    'json',
    'yaml',
    'yml',
    'csv',
    'log',
    'py',
    'dart',
    'js',
    'ts',
    'html',
    'css',
    'ps1',
    'xml',
    'ini',
    'toml',
    'sql',
    'java',
    'kt',
    'swift',
    'c',
    'cpp',
    'h',
    'hpp',
    'cs',
    'sh',
    'bat',
  };

  final TextEditingController _controller =
      TextEditingController();

  final ScrollController _scrollController =
      ScrollController();

  final List<_ChatTurn> _turns = <_ChatTurn>[];
  final List<_Attachment> _attachments = <_Attachment>[];

  bool _busy = false;
  bool _turboMillion = true;
  _ChatMode _mode = _ChatMode.normal;

  String _scale = '-';
  int _capacity = 0;
  int _activeWorkers = 0;
  int _batches = 0;
  String _factory = '-';
  String _provider = '-';
  String _toolStatus = '';

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _handleMode(_ChatMode mode) async {
    if (!mounted) return;

    setState(() {
      _mode = mode;
      _toolStatus = '';
    });

    switch (mode) {
      case _ChatMode.files:
        await _pickFiles();

      case _ChatMode.library:
        await _pickLibraryFolder();

      case _ChatMode.calendar:
        await _openExternal(
          'https://calendar.google.com/',
        );

        if (!mounted) return;

        setState(() {
          _toolStatus =
              'เปิด Google Calendar แล้ว '
              'คุณสามารถพิมพ์งานที่ต้องการให้ Friend ช่วยต่อได้';
        });

      case _ChatMode.web:
        if (!mounted) return;

        setState(() {
          _toolStatus =
              'พิมพ์คำค้นแล้วกดส่ง '
              'ระบบจะเปิดผลค้นหาเว็บจริงพร้อมส่งคำถามให้ Friend';
        });

      case _ChatMode.image:
        if (!mounted) return;

        setState(() {
          _toolStatus =
              'โหมดสร้างรูปภาพจะให้ Friend เตรียม '
              'image brief/prompt สำหรับ Provider ที่เชื่อมอยู่';
        });

      case _ChatMode.deepResearch:
        if (!mounted) return;

        setState(() {
          _toolStatus =
              'Deep Research ใช้ complexity/parallelism สูงขึ้น '
              'และเปิด research + quality skills';
        });

      case _ChatMode.normal:
        break;
    }
  }

  Future<void> _pickFiles() async {
    final paths = await _nativeOpenFiles();

    if (!mounted || paths.isEmpty) return;

    final List<_Attachment> added = <_Attachment>[];

    for (final path in paths) {
      final attachment = await _attachmentFromFile(path);

      if (attachment != null) {
        added.add(attachment);
      }
    }

    if (!mounted) return;

    setState(() {
      _attachments.addAll(added);
      _toolStatus = added.isEmpty
          ? 'ไม่พบไฟล์ที่อ่านได้'
          : 'เพิ่มไฟล์ ${added.length} รายการแล้ว';
    });
  }

  Future<void> _pickLibraryFolder() async {
    final path = await _nativePickFolder();

    if (!mounted || path == null || path.isEmpty) {
      return;
    }

    final directory = Directory(path);

    if (!directory.existsSync()) {
      return;
    }

    final List<String> lines = <String>[];

    try {
      await for (final entity in directory.list(
        recursive: true,
        followLinks: false,
      )) {
        if (entity is File) {
          final relative = entity.path
                  .startsWith(directory.path)
              ? entity.path
                  .substring(directory.path.length)
                  .replaceFirst(
                    RegExp(r'^[\\/]'),
                    '',
                  )
              : entity.path;

          lines.add(relative);

          if (lines.length >= 120) {
            break;
          }
        }
      }
    } catch (_) {
      lines.clear();
    }

    final label = _leafName(path);

    final context = <String>[
      'Local library folder: $path',
      'Files visible to the selected library context '
          '(${lines.length}${lines.length >= 120 ? '+' : ''}):',
      ...lines.map((item) => '- $item'),
    ].join('\n');

    if (!mounted) return;

    setState(() {
      _attachments.add(
        _Attachment(
          path: path,
          label: 'Library: $label',
          context: context,
        ),
      );

      _toolStatus = 'เพิ่มคลัง $label แล้ว';
    });
  }

  Future<_Attachment?> _attachmentFromFile(
    String path,
  ) async {
    final file = File(path);

    if (!file.existsSync()) {
      return null;
    }

    final name = _leafName(path);
    final size = await file.length();

    final extension = name.contains('.')
        ? name.split('.').last.toLowerCase()
        : '';

    final context = StringBuffer()
      ..writeln('Attached local file: $name')
      ..writeln('Path: $path')
      ..writeln('Size: $size bytes');

    if (_textExtensions.contains(extension) &&
        size <= _maxTextFileBytes) {
      try {
        final text = await file.readAsString();

        context
          ..writeln('Content:')
          ..write(text);
      } catch (_) {
        context.writeln(
          'Content could not be decoded as UTF-8 text.',
        );
      }
    } else {
      context.writeln(
        'Binary or large file: metadata only in this runtime.',
      );
    }

    return _Attachment(
      path: path,
      label: name,
      context: context.toString(),
    );
  }

  String _attachmentContext() {
    if (_attachments.isEmpty) {
      return '';
    }

    final StringBuffer output =
        StringBuffer('\n\nOWNER LOCAL CONTEXT\n');

    for (final attachment in _attachments) {
      if (output.length + attachment.context.length >
          _maxAttachmentContextChars) {
        output.writeln(
          '\n[Attachment context truncated at '
          '$_maxAttachmentContextChars characters]',
        );
        break;
      }

      output
        ..writeln('\n--- ${attachment.label} ---')
        ..writeln(attachment.context);
    }

    return output.toString();
  }

  Future<void> _send() async {
    final visibleText = _controller.text.trim();

    if (visibleText.isEmpty || _busy) {
      return;
    }

    if (_mode == _ChatMode.web) {
      final searchUrl =
          'https://www.google.com/search?q='
          '${Uri.encodeQueryComponent(visibleText)}';

      await _openExternal(searchUrl);

      if (!mounted) {
        return;
      }
    }

    var prompt = visibleText;

    switch (_mode) {
      case _ChatMode.image:
        prompt =
            'Prepare a production-ready image generation brief '
            'and prompt for this request. '
            'Do not claim an image was generated unless the '
            'connected provider actually returns one.\n\n'
            '$visibleText';

      case _ChatMode.web:
        prompt =
            'Web-search mode is active. The system opened a '
            'real browser search for this query. '
            'Do not claim to have read browser results unless '
            'the user supplies them. '
            'Analyze the query and explain what to verify.\n\n'
            '$visibleText';

      case _ChatMode.calendar:
        prompt =
            'Google Calendar mode is active and the calendar '
            'was opened on the desktop. '
            'Help plan or interpret the requested schedule '
            'without claiming calendar data that was not supplied.\n\n'
            '$visibleText';

      case _ChatMode.normal:
      case _ChatMode.files:
      case _ChatMode.library:
      case _ChatMode.deepResearch:
        break;
    }

    prompt += _attachmentContext();

    if (!mounted) {
      return;
    }

    setState(() {
      _busy = true;
    });

    try {
      final response = await widget.api.chat(
        prompt,
        complexity:
            _mode == _ChatMode.deepResearch ? 9 : 6,
        risk: 3,
        parallelism:
            _mode == _ChatMode.deepResearch ? 16 : 8,
        helperBudget:
            _turboMillion ? 1000000 : 0,
        requestedSkills: _mode.skills,
      );

      final decision = _mapFromDynamic(
        response['decision'],
      );

      final helpers = _mapFromDynamic(
        response['helpers'],
      );

      final factory = _mapFromDynamic(
        response['factory'],
      );

      final answer = response['text']?.toString() ?? '';

      final provider =
          response['provider']?.toString() ?? '-';

      final capacity =
          _intFromDynamic(decision['capacity']);

      final activeWorkers =
          _intFromDynamic(helpers['active_workers']);

      final batches =
          _intFromDynamic(helpers['batches']);

      final factoryStages =
          _listFromDynamic(factory['stages']);

      if (!mounted) {
        return;
      }

      setState(() {
        _turns.add(
          _ChatTurn(
            user: visibleText,
            answer: answer,
            provider: provider,
          ),
        );

        _provider = provider;
        _scale = decision['scale']?.toString() ?? '-';
        _capacity = capacity;
        _activeWorkers = activeWorkers;
        _batches = batches;
        _factory = factoryStages.join(' → ');

        _controller.clear();
      });

      _scrollToBottom();
    } catch (error) {
      if (!mounted) {
        return;
      }

      setState(() {
        _turns.add(
          _ChatTurn(
            user: visibleText,
            answer: 'Friend Service error: $error',
            provider: '-',
          ),
        );
      });

      _scrollToBottom();
    } finally {
      if (mounted) {
        setState(() {
          _busy = false;
        });
      }
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_scrollController.hasClients) {
        return;
      }

      final position = _scrollController.position;

      _scrollController.animateTo(
        position.maxScrollExtent,
        duration: const Duration(milliseconds: 220),
        curve: Curves.easeOut,
      );
    });
  }

  Future<List<String>> _nativeOpenFiles() async {
    if (!Platform.isWindows) {
      if (mounted) {
        setState(() {
          _toolStatus =
              'ตัวเลือกไฟล์ V3 รองรับ Windows desktop '
              'ใน build นี้';
        });
      }

      return const <String>[];
    }

    const script = r'''
Add-Type -AssemblyName System.Windows.Forms
$dialog = New-Object System.Windows.Forms.OpenFileDialog
$dialog.Multiselect = $true
$dialog.Filter = 'All files (*.*)|*.*|Documents (*.txt;*.md;*.json;*.csv;*.pdf)|*.txt;*.md;*.json;*.csv;*.pdf|Images (*.png;*.jpg;*.jpeg;*.webp)|*.png;*.jpg;*.jpeg;*.webp'
if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
  $dialog.FileNames | ForEach-Object {
    [Console]::Out.WriteLine($_)
  }
}
''';

    try {
      final result = await Process.run(
        'powershell.exe',
        const <String>[
          '-NoProfile',
          '-STA',
          '-Command',
          script,
        ],
      );

      if (result.exitCode != 0) {
        throw ProcessException(
          'powershell.exe',
          const <String>[],
          result.stderr.toString(),
          result.exitCode,
        );
      }

      return result.stdout
          .toString()
          .split(RegExp(r'[\r\n]+'))
          .map((item) => item.trim())
          .where((item) => item.isNotEmpty)
          .toList();
    } catch (error) {
      if (mounted) {
        setState(() {
          _toolStatus =
              'เปิดตัวเลือกไฟล์ไม่สำเร็จ: $error';
        });
      }

      return const <String>[];
    }
  }

  Future<String?> _nativePickFolder() async {
    if (!Platform.isWindows) {
      if (mounted) {
        setState(() {
          _toolStatus =
              'ตัวเลือกคลัง V3 รองรับ Windows desktop '
              'ใน build นี้';
        });
      }

      return null;
    }

    const script = r'''
Add-Type -AssemblyName System.Windows.Forms
$dialog = New-Object System.Windows.Forms.FolderBrowserDialog
$dialog.Description = 'เลือกโฟลเดอร์คลังสำหรับ Research OS Friend'
if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
  [Console]::Out.WriteLine($dialog.SelectedPath)
}
''';

    try {
      final result = await Process.run(
        'powershell.exe',
        const <String>[
          '-NoProfile',
          '-STA',
          '-Command',
          script,
        ],
      );

      if (result.exitCode != 0) {
        return null;
      }

      final value = result.stdout.toString().trim();

      return value.isEmpty ? null : value;
    } catch (error) {
      if (mounted) {
        setState(() {
          _toolStatus =
              'เปิดตัวเลือกคลังไม่สำเร็จ: $error';
        });
      }

      return null;
    }
  }

  Future<void> _openExternal(String url) async {
    if (!Platform.isWindows) {
      return;
    }

    try {
      await Process.start(
        'rundll32.exe',
        <String>[
          'url.dll,FileProtocolHandler',
          url,
        ],
      );
    } catch (error) {
      if (mounted) {
        setState(() {
          _toolStatus =
              'เปิดลิงก์ไม่สำเร็จ: $error';
        });
      }
    }
  }

  static Map<String, dynamic> _mapFromDynamic(
    dynamic value,
  ) {
    if (value is Map<String, dynamic>) {
      return value;
    }

    if (value is Map) {
      return Map<String, dynamic>.from(value);
    }

    return <String, dynamic>{};
  }

  static List<dynamic> _listFromDynamic(
    dynamic value,
  ) {
    if (value is List) {
      return value;
    }

    return const <dynamic>[];
  }

  static int _intFromDynamic(dynamic value) {
    if (value is num) {
      return value.toInt();
    }

    return int.tryParse(value?.toString() ?? '') ?? 0;
  }

  static String _leafName(String path) {
    final normalized = path.replaceAll('\\', '/');

    final segments = normalized
        .split('/')
        .where((item) => item.isNotEmpty)
        .toList();

    return segments.isEmpty ? path : segments.last;
  }

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final availableWidth =
            constraints.maxWidth - 40;

        final width = availableWidth.clamp(
          0.0,
          1040.0,
        );

        return Center(
          child: SizedBox(
            width: width,
            child: Padding(
              padding: const EdgeInsets.fromLTRB(
                8,
                16,
                8,
                16,
              ),
              child: Column(
                children: <Widget>[
                  _RuntimeStrip(
                    turboMillion: _turboMillion,
                    onTurboChanged: (value) {
                      setState(
                        () => _turboMillion = value,
                      );
                    },
                    scale: _scale,
                    capacity: _capacity,
                    workers: _activeWorkers,
                    batches: _batches,
                    provider: _provider,
                    factory: _factory,
                  ),
                  const SizedBox(height: 10),
                  Expanded(
                    child: _turns.isEmpty
                        ? _EmptyChat(mode: _mode)
                        : ListView.builder(
                            controller: _scrollController,
                            padding:
                                const EdgeInsets.symmetric(
                              vertical: 12,
                            ),
                            itemCount: _turns.length,
                            itemBuilder:
                                (context, index) {
                              return _ConversationTurn(
                                turn: _turns[index],
                              );
                            },
                          ),
                  ),
                  if (_attachments.isNotEmpty) ...<Widget>[
                    Align(
                      alignment: Alignment.centerLeft,
                      child: Wrap(
                        spacing: 8,
                        runSpacing: 6,
                        children: _attachments.map(
                          (attachment) {
                            return InputChip(
                              avatar: const Icon(
                                Icons.description_outlined,
                                size: 16,
                              ),
                              label: ConstrainedBox(
                                constraints:
                                    const BoxConstraints(
                                  maxWidth: 260,
                                ),
                                child: Text(
                                  attachment.label,
                                  overflow:
                                      TextOverflow.ellipsis,
                                ),
                              ),
                              onDeleted: () {
                                setState(() {
                                  _attachments.remove(
                                    attachment,
                                  );
                                });
                              },
                            );
                          },
                        ).toList(),
                      ),
                    ),
                    const SizedBox(height: 6),
                  ],
                  if (_toolStatus.isNotEmpty)
                    Align(
                      alignment: Alignment.centerLeft,
                      child: Padding(
                        padding: const EdgeInsets.only(
                          left: 10,
                          bottom: 6,
                        ),
                        child: Text(
                          _toolStatus,
                          style: Theme.of(context)
                              .textTheme
                              .bodySmall
                              ?.copyWith(
                                color: Theme.of(context)
                                    .colorScheme
                                    .onSurfaceVariant,
                              ),
                        ),
                      ),
                    ),
                  _Composer(
                    controller: _controller,
                    busy: _busy,
                    mode: _mode,
                    onModeSelected: _handleMode,
                    onSend: _send,
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }
}

class _RuntimeStrip extends StatelessWidget {
  const _RuntimeStrip({
    required this.turboMillion,
    required this.onTurboChanged,
    required this.scale,
    required this.capacity,
    required this.workers,
    required this.batches,
    required this.provider,
    required this.factory,
  });

  final bool turboMillion;
  final ValueChanged<bool> onTurboChanged;
  final String scale;
  final int capacity;
  final int workers;
  final int batches;
  final String provider;
  final String factory;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 42,
      child: ListView(
        scrollDirection: Axis.horizontal,
        children: <Widget>[
          FilterChip(
            key: const Key('turbo-million-v3'),
            selected: turboMillion,
            onSelected: onTurboChanged,
            label: const Text(
              'Turbo Helpers 1,000,000',
            ),
          ),
          const SizedBox(width: 8),
          Chip(
            label: Text('Brain scale: $scale'),
          ),
          const SizedBox(width: 8),
          Chip(
            label: Text(
              'Logical capacity: $capacity',
            ),
          ),
          const SizedBox(width: 8),
          Chip(
            label: Text(
              'Active workers: $workers',
            ),
          ),
          const SizedBox(width: 8),
          Chip(
            label: Text('Batches: $batches'),
          ),
          if (provider != '-') ...<Widget>[
            const SizedBox(width: 8),
            Chip(
              avatar: const Icon(
                Icons.smart_toy_outlined,
                size: 16,
              ),
              label: Text(
                'Provider: $provider',
              ),
            ),
          ],
          if (factory != '-') ...<Widget>[
            const SizedBox(width: 8),
            Chip(
              label: Text(
                'Factory: $factory',
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _EmptyChat extends StatelessWidget {
  const _EmptyChat({
    required this.mode,
  });

  final _ChatMode mode;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Center(
      child: Padding(
        padding: const EdgeInsets.only(bottom: 70),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            Container(
              width: 58,
              height: 58,
              decoration: BoxDecoration(
                color: colorScheme.primaryContainer,
                shape: BoxShape.circle,
              ),
              child: Icon(
                Icons.psychology,
                color: colorScheme.onPrimaryContainer,
              ),
            ),
            const SizedBox(height: 18),
            Text(
              'วันนี้ให้ Research OS Friend ช่วยอะไร?',
              textAlign: TextAlign.center,
              style: Theme.of(context)
                  .textTheme
                  .headlineSmall
                  ?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
            ),
            const SizedBox(height: 8),
            Text(
              mode == _ChatMode.normal
                  ? 'พร้อมคุย วิเคราะห์ วางแผน '
                    'และใช้ความจำของ Owner'
                  : '${mode.title} • ${mode.subtitle}',
              textAlign: TextAlign.center,
              style: Theme.of(context)
                  .textTheme
                  .bodyMedium
                  ?.copyWith(
                    color: colorScheme.onSurfaceVariant,
                  ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ConversationTurn extends StatelessWidget {
  const _ConversationTurn({
    required this.turn,
  });

  final _ChatTurn turn;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Padding(
      padding: const EdgeInsets.only(bottom: 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          Align(
            alignment: Alignment.centerRight,
            child: Container(
              constraints: const BoxConstraints(
                maxWidth: 720,
              ),
              padding: const EdgeInsets.symmetric(
                horizontal: 18,
                vertical: 12,
              ),
              decoration: BoxDecoration(
                color: colorScheme.secondaryContainer,
                borderRadius: BorderRadius.circular(20),
              ),
              child: SelectableText(turn.user),
            ),
          ),
          const SizedBox(height: 18),
          Row(
            crossAxisAlignment:
                CrossAxisAlignment.start,
            children: <Widget>[
              CircleAvatar(
                radius: 16,
                backgroundColor:
                    colorScheme.primaryContainer,
                child: Icon(
                  Icons.psychology,
                  size: 18,
                  color: colorScheme
                      .onPrimaryContainer,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment:
                      CrossAxisAlignment.start,
                  children: <Widget>[
                    SelectableText(
                      turn.answer,
                      key: const Key(
                        'friend-v3-answer',
                      ),
                      style: Theme.of(context)
                          .textTheme
                          .bodyLarge
                          ?.copyWith(
                            height: 1.55,
                          ),
                    ),
                    if (turn.provider != '-') ...<Widget>[
                      const SizedBox(height: 8),
                      Text(
                        'Provider: ${turn.provider}',
                        style: Theme.of(context)
                            .textTheme
                            .bodySmall
                            ?.copyWith(
                              color: colorScheme
                                  .onSurfaceVariant,
                            ),
                      ),
                    ],
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _Composer extends StatelessWidget {
  const _Composer({
    required this.controller,
    required this.busy,
    required this.mode,
    required this.onModeSelected,
    required this.onSend,
  });

  final TextEditingController controller;
  final bool busy;
  final _ChatMode mode;
  final Future<void> Function(_ChatMode)
      onModeSelected;
  final VoidCallback onSend;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Material(
      elevation: 3,
      borderRadius: BorderRadius.circular(28),
      color: colorScheme.surface,
      child: Container(
        padding: const EdgeInsets.fromLTRB(
          10,
          8,
          10,
          8,
        ),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(28),
          border: Border.all(
            color: colorScheme.outlineVariant,
          ),
        ),
        child: Column(
          children: <Widget>[
            if (mode != _ChatMode.normal)
              Align(
                alignment: Alignment.centerLeft,
                child: Padding(
                  padding: const EdgeInsets.only(
                    left: 8,
                    bottom: 4,
                  ),
                  child: InputChip(
                    avatar: Icon(
                      mode.icon,
                      size: 17,
                    ),
                    label: Text(mode.title),
                    onDeleted: () {
                      onModeSelected(
                        _ChatMode.normal,
                      );
                    },
                  ),
                ),
              ),
            Row(
              crossAxisAlignment:
                  CrossAxisAlignment.end,
              children: <Widget>[
                PopupMenuButton<_ChatMode>(
                  key: const Key(
                    'friend-v3-tools-menu',
                  ),
                  tooltip: 'เพิ่มเครื่องมือ',
                  onSelected: (value) {
                    onModeSelected(value);
                  },
                  position: PopupMenuPosition.over,
                  itemBuilder: (context) {
                    return _ChatMode.values
                        .where(
                          (item) =>
                              item != _ChatMode.normal,
                        )
                        .map(
                          (item) {
                            return PopupMenuItem<
                                _ChatMode>(
                              value: item,
                              child: SizedBox(
                                width: 330,
                                child: Row(
                                  children: <Widget>[
                                    Icon(
                                      item.icon,
                                      size: 22,
                                    ),
                                    const SizedBox(
                                      width: 12,
                                    ),
                                    Expanded(
                                      child: Column(
                                        crossAxisAlignment:
                                            CrossAxisAlignment
                                                .start,
                                        mainAxisSize:
                                            MainAxisSize.min,
                                        children: <Widget>[
                                          Text(
                                            item.title,
                                            style:
                                                const TextStyle(
                                              fontWeight:
                                                  FontWeight
                                                      .w600,
                                            ),
                                          ),
                                          const SizedBox(
                                            height: 2,
                                          ),
                                          Text(
                                            item.subtitle,
                                            style: Theme.of(
                                              context,
                                            )
                                                .textTheme
                                                .bodySmall,
                                          ),
                                        ],
                                      ),
                                    ),
                                    if (mode == item)
                                      const Icon(
                                        Icons.check,
                                        size: 18,
                                      ),
                                  ],
                                ),
                              ),
                            );
                          },
                        )
                        .toList();
                  },
                  child: Container(
                    width: 42,
                    height: 42,
                    decoration: BoxDecoration(
                      color: colorScheme
                          .surfaceContainerHighest,
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(Icons.add),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: TextField(
                    key: const Key(
                      'friend-v3-input',
                    ),
                    controller: controller,
                    minLines: 1,
                    maxLines: 6,
                    textInputAction:
                        TextInputAction.newline,
                    decoration:
                        const InputDecoration(
                      border: InputBorder.none,
                      enabledBorder:
                          InputBorder.none,
                      focusedBorder:
                          InputBorder.none,
                      hintText:
                          'ถาม Research OS Friend…',
                      contentPadding:
                          EdgeInsets.symmetric(
                        horizontal: 6,
                        vertical: 11,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 6),
                PopupMenuButton<_ChatMode>(
                  tooltip: 'โหมดการทำงาน',
                  onSelected: (value) {
                    onModeSelected(value);
                  },
                  itemBuilder: (context) {
                    return _ChatMode.values.map(
                      (item) {
                        return PopupMenuItem<
                            _ChatMode>(
                          value: item,
                          child: Row(
                            children: <Widget>[
                              Icon(
                                item.icon,
                                size: 19,
                              ),
                              const SizedBox(
                                width: 9,
                              ),
                              Text(item.title),
                              if (item == mode) ...<Widget>[
                                const Spacer(),
                                const Icon(
                                  Icons.check,
                                  size: 17,
                                ),
                              ],
                            ],
                          ),
                        );
                      },
                    ).toList();
                  },
                  child: Padding(
                    padding:
                        const EdgeInsets.symmetric(
                      horizontal: 8,
                      vertical: 10,
                    ),
                    child: Row(
                      mainAxisSize:
                          MainAxisSize.min,
                      children: <Widget>[
                        Text(mode.title),
                        const SizedBox(width: 3),
                        const Icon(
                          Icons.keyboard_arrow_down,
                          size: 18,
                        ),
                      ],
                    ),
                  ),
                ),
                IconButton(
                  tooltip:
                      'Voice input จะเชื่อมในขั้นถัดไป',
                  onPressed: null,
                  icon: const Icon(
                    Icons.mic_none,
                  ),
                ),
                FilledButton(
                  key: const Key(
                    'friend-v3-send',
                  ),
                  onPressed:
                      busy ? null : onSend,
                  style: FilledButton.styleFrom(
                    shape: const CircleBorder(),
                    minimumSize: const Size(
                      44,
                      44,
                    ),
                    padding:
                        const EdgeInsets.all(12),
                  ),
                  child: busy
                      ? const SizedBox.square(
                          dimension: 18,
                          child:
                              CircularProgressIndicator(
                            strokeWidth: 2,
                          ),
                        )
                      : const Icon(
                          Icons.arrow_upward,
                          size: 20,
                        ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _Capabilities extends StatelessWidget {
  const _Capabilities({
    required this.api,
    this.startup,
  });

  final OwnerFriendApi api;
  final Map<String, dynamic>? startup;

  @override
  Widget build(BuildContext context) {
    final startupStatus = startup?['status'];

    final Future<Map<String, dynamic>> future =
        startupStatus is Map
            ? Future<Map<String, dynamic>>.value(
                Map<String, dynamic>.from(
                  startupStatus,
                ),
              )
            : api.status();

    return FutureBuilder<Map<String, dynamic>>(
      future: future,
      builder: (context, snapshot) {
        if (snapshot.connectionState ==
            ConnectionState.waiting) {
          return const Center(
            child: CircularProgressIndicator(),
          );
        }

        if (snapshot.hasError) {
          return Center(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: SelectableText(
                'ไม่สามารถโหลด Capabilities ได้:\n'
                '${snapshot.error}',
              ),
            ),
          );
        }

        if (!snapshot.hasData) {
          return const Center(
            child: Text(
              'ไม่มีข้อมูล Capabilities',
            ),
          );
        }

        final status = snapshot.data!;

        final profiles = _mapFromDynamic(
          status['brain_profiles'],
        );

        final helper = _mapFromDynamic(
          status['helper_scheduler'],
        );

        final capabilities = _listFromDynamic(
          status['capabilities'],
        ).map((item) => item.toString()).toList();

        return ListView(
          padding: const EdgeInsets.all(28),
          children: <Widget>[
            Text(
              'Friend Complete Architecture',
              style: Theme.of(context)
                  .textTheme
                  .headlineSmall
                  ?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
            ),
            const SizedBox(height: 18),
            _InfoCard(
              title: 'Brain profiles',
              icon: Icons.psychology_outlined,
              child: Wrap(
                spacing: 8,
                runSpacing: 8,
                children: profiles.entries.map(
                  (entry) {
                    return Chip(
                      label: Text(
                        '${entry.key} = ${entry.value}',
                      ),
                    );
                  },
                ).toList(),
              ),
            ),
            const SizedBox(height: 14),
            _InfoCard(
              title: 'Helper scheduler',
              icon: Icons.hub_outlined,
              child: Text(
                'Logical helpers: '
                '${helper['max_logical_helpers'] ?? '-'}'
                ' • Active workers: '
                '${helper['max_active_workers'] ?? '-'}',
              ),
            ),
            const SizedBox(height: 14),
            _InfoCard(
              title: 'Capabilities',
              icon: Icons.auto_awesome_outlined,
              child: Wrap(
                spacing: 8,
                runSpacing: 8,
                children: capabilities.map(
                  (name) {
                    return Chip(
                      label: Text(name),
                    );
                  },
                ).toList(),
              ),
            ),
          ],
        );
      },
    );
  }

  static Map<String, dynamic> _mapFromDynamic(
    dynamic value,
  ) {
    if (value is Map<String, dynamic>) {
      return value;
    }

    if (value is Map) {
      return Map<String, dynamic>.from(value);
    }

    return <String, dynamic>{};
  }

  static List<dynamic> _listFromDynamic(
    dynamic value,
  ) {
    if (value is List) {
      return value;
    }

    return const <dynamic>[];
  }
}

class _InfoCard extends StatelessWidget {
  const _InfoCard({
    required this.title,
    required this.icon,
    required this.child,
  });

  final String title;
  final IconData icon;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 0,
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment:
              CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              children: <Widget>[
                Icon(icon),
                const SizedBox(width: 10),
                Text(
                  title,
                  style: Theme.of(context)
                      .textTheme
                      .titleMedium
                      ?.copyWith(
                        fontWeight: FontWeight.w700,
                      ),
                ),
              ],
            ),
            const SizedBox(height: 14),
            child,
          ],
        ),
      ),
    );
  }
}

class _Memory extends StatelessWidget {
  const _Memory({
    required this.api,
  });

  final OwnerFriendApi api;

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<Map<String, dynamic>>(
      future: api.memory(),
      builder: (context, snapshot) {
        if (snapshot.connectionState ==
            ConnectionState.waiting) {
          return const Center(
            child: CircularProgressIndicator(),
          );
        }

        if (snapshot.hasError) {
          return Center(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: SelectableText(
                'ไม่สามารถโหลด Memory ได้:\n'
                '${snapshot.error}',
              ),
            ),
          );
        }

        if (!snapshot.hasData) {
          return const Center(
            child: Text(
              'ไม่มีข้อมูล Memory',
            ),
          );
        }

        final rawItems = snapshot.data!['items'];

        final items = rawItems is List
            ? rawItems
            : const <dynamic>[];

        if (items.isEmpty) {
          return const Center(
            child: Text(
              'ยังไม่มีความจำใน profile/session นี้',
            ),
          );
        }

        return ListView.separated(
          padding: const EdgeInsets.all(28),
          itemCount: items.length,
          separatorBuilder: (_, __) =>
              const SizedBox(height: 10),
          itemBuilder: (context, index) {
            final rawItem = items[index];

            final item = rawItem is Map
                ? Map<String, dynamic>.from(
                    rawItem,
                  )
                : <String, dynamic>{};

            final kind =
                item['kind']?.toString() ?? '';

            return Card(
              elevation: 0,
              child: ListTile(
                leading: CircleAvatar(
                  child: Icon(
                    kind == 'request'
                        ? Icons.person_outline
                        : Icons.psychology_outlined,
                  ),
                ),
                title: Text(
                  kind.isEmpty ? 'memory' : kind,
                ),
                subtitle: Text(
                  item['text']?.toString() ?? '',
                ),
              ),
            );
          },
        );
      },
    );
  }
}

class _Provider extends StatefulWidget {
  const _Provider({
    required this.api,
  });

  final OwnerFriendApi api;

  @override
  State<_Provider> createState() => _ProviderState();
}

class _ProviderState extends State<_Provider> {
  final TextEditingController _baseUrl =
      TextEditingController();

  final TextEditingController _model =
      TextEditingController();

  final TextEditingController _apiKey =
      TextEditingController();

  Map<String, dynamic>? _status;

  String _message = '';
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _baseUrl.dispose();
    _model.dispose();
    _apiKey.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    try {
      final status =
          await widget.api.providerStatus();

      if (!mounted) {
        return;
      }

      setState(() {
        _status = status;
        _baseUrl.text =
            status['base_url']?.toString() ?? '';
        _model.text =
            status['model']?.toString() ?? '';
      });
    } catch (error) {
      if (mounted) {
        setState(() {
          _message = '$error';
        });
      }
    }
  }

  Future<void> _saveAndTest() async {
    if (_busy) {
      return;
    }

    if (!mounted) {
      return;
    }

    setState(() {
      _busy = true;
      _message = '';
    });

    try {
      final baseUrl = _baseUrl.text.trim();
      final model = _model.text.trim();
      final apiKey = _apiKey.text.trim();

      if (baseUrl.isEmpty) {
        throw const FormatException(
          'Base URL cannot be empty.',
        );
      }

      if (model.isEmpty) {
        throw const FormatException(
          'Model cannot be empty.',
        );
      }

      final saved =
          await widget.api.configureProvider(
        baseUrl: baseUrl,
        model: model,
        apiKey: apiKey.isEmpty ? null : apiKey,
      );

      _apiKey.clear();

      final tested =
          await widget.api.testProvider();

      if (!mounted) {
        return;
      }

      setState(() {
        _status = saved;
        _message = tested['connected'] == true
            ? 'Provider connected'
            : 'Provider test failed: '
                '${tested['error'] ?? 'unknown'}';
      });
    } catch (error) {
      if (mounted) {
        setState(() {
          _message = '$error';
        });
      }
    } finally {
      if (mounted) {
        setState(() {
          _busy = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final credentialPresent =
        _status?['credential_present'] == true;

    return ListView(
      padding: const EdgeInsets.all(28),
      children: <Widget>[
        Text(
          'OpenAI-compatible Provider',
          style: Theme.of(context)
              .textTheme
              .headlineSmall
              ?.copyWith(
                fontWeight: FontWeight.w700,
              ),
        ),
        const SizedBox(height: 8),
        Text(
          'Credential: '
          '${credentialPresent ? 'stored securely' : 'not configured'}'
          ' • backend: '
          '${_status?['secret_backend'] ?? '-'}',
        ),
        const SizedBox(height: 20),
        TextField(
          key: const Key(
            'provider-v3-base-url',
          ),
          controller: _baseUrl,
          keyboardType: TextInputType.url,
          decoration: const InputDecoration(
            labelText: 'Base URL',
          ),
        ),
        const SizedBox(height: 12),
        TextField(
          key: const Key(
            'provider-v3-model',
          ),
          controller: _model,
          decoration: const InputDecoration(
            labelText: 'Model',
          ),
        ),
        const SizedBox(height: 12),
        TextField(
          key: const Key(
            'provider-v3-api-key',
          ),
          controller: _apiKey,
          obscureText: true,
          decoration: const InputDecoration(
            labelText:
                'API key (leave blank to keep existing)',
          ),
        ),
        const SizedBox(height: 16),
        FilledButton.icon(
          key: const Key(
            'provider-v3-save-test',
          ),
          onPressed:
              _busy ? null : _saveAndTest,
          icon: const Icon(Icons.link),
          label: Text(
            _busy
                ? 'Testing...'
                : 'Save & Test Connection',
          ),
        ),
        if (_message.isNotEmpty)
          Padding(
            padding: const EdgeInsets.only(
              top: 16,
            ),
            child: SelectableText(
              _message,
              key: const Key(
                'provider-v3-message',
              ),
            ),
          ),
      ],
    );
  }
}