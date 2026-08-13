class SystemSnapshot {
  const SystemSnapshot({
    required this.rootPath,
    required this.installed,
    required this.gitAvailable,
    required this.ghAvailable,
    required this.githubAuthenticated,
    required this.workerState,
    required this.bundleCount,
    required this.mirrorCount,
    required this.repositoryCount,
    required this.restorePointCount,
    required this.lastLogLines,
    required this.bootstrap,
  });

  final String? rootPath;
  final bool installed;
  final bool gitAvailable;
  final bool ghAvailable;
  final bool githubAuthenticated;
  final String workerState;
  final int bundleCount;
  final int mirrorCount;
  final int repositoryCount;
  final int restorePointCount;
  final List<String> lastLogLines;
  final Map<String, dynamic>? bootstrap;

  bool get rootReady => rootPath != null;
  bool get workerInstalled => workerState.toLowerCase() != 'not installed';
  bool get workerRunning => workerState.toLowerCase() == 'running';
}
