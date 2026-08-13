class RepositoryRecord {
  const RepositoryRecord({
    required this.name,
    required this.folderPath,
    required this.hasBundle,
    required this.hasMirrorArchive,
    required this.snapshotFiles,
    required this.bundleBytes,
  });

  final String name;
  final String folderPath;
  final bool hasBundle;
  final bool hasMirrorArchive;
  final int snapshotFiles;
  final int bundleBytes;
}
