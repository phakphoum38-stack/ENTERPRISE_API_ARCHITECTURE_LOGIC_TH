class AppSettings {
  const AppSettings({
    this.githubOwner = 'phakphoum38-stack',
    this.autoRefreshSeconds = 20,
    this.autoSync = true,
    this.preferredRootPath = '',
  });

  final String githubOwner;
  final int autoRefreshSeconds;
  final bool autoSync;
  final String preferredRootPath;

  AppSettings copyWith({
    String? githubOwner,
    int? autoRefreshSeconds,
    bool? autoSync,
    String? preferredRootPath,
  }) {
    return AppSettings(
      githubOwner: githubOwner ?? this.githubOwner,
      autoRefreshSeconds: autoRefreshSeconds ?? this.autoRefreshSeconds,
      autoSync: autoSync ?? this.autoSync,
      preferredRootPath: preferredRootPath ?? this.preferredRootPath,
    );
  }

  Map<String, dynamic> toJson() => {
        'githubOwner': githubOwner,
        'autoRefreshSeconds': autoRefreshSeconds,
        'autoSync': autoSync,
        'preferredRootPath': preferredRootPath,
      };

  factory AppSettings.fromJson(Map<String, dynamic> json) {
    return AppSettings(
      githubOwner: '${json['githubOwner'] ?? 'phakphoum38-stack'}',
      autoRefreshSeconds: (json['autoRefreshSeconds'] as num?)?.toInt() ?? 20,
      autoSync: json['autoSync'] != false,
      preferredRootPath: '${json['preferredRootPath'] ?? ''}',
    );
  }
}
