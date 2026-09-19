/// Platform-neutral application boundary.
library;

enum ResearchOSPlatform { windows, macos, ios, android, web, linux, other }

final class PlatformContract {
  const PlatformContract({
    required this.platform,
    required this.applicationIdentity,
    required this.runnerIdentity,
  });

  final ResearchOSPlatform platform;
  final String applicationIdentity;
  final String runnerIdentity;
}
