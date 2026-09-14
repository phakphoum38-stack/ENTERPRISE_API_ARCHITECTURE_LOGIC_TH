import 'package:flutter/material.dart';

import '../api/research_os_api_client.dart';
import 'conversation_core.dart';
import 'friend_workspace.dart';
import 'v5_capability.dart';
import 'v5_workspace_route.dart';

/// Semantic host for V5 workspaces.
///
/// The host owns the Friend conversation controller so the conversation
/// survives workspace changes while the host remains mounted. AppShell can
/// adopt this host incrementally without moving conversation state into each
/// individual workspace.
class ResearchOSV5WorkspaceHost extends StatefulWidget {
  const ResearchOSV5WorkspaceHost({
    required this.apiClient,
    required this.level,
    required this.workspace,
    this.childBuilder,
    super.key,
  });

  final ResearchOSApiClient apiClient;
  final ResearchOSUserLevel level;
  final ResearchOSWorkspace workspace;
  final Widget Function(
    BuildContext context,
    ResearchOSWorkspaceRoute route,
  )? childBuilder;

  @override
  State<ResearchOSV5WorkspaceHost> createState() =>
      _ResearchOSV5WorkspaceHostState();
}

class _ResearchOSV5WorkspaceHostState
    extends State<ResearchOSV5WorkspaceHost> {
  late final ResearchOSConversationController _conversation =
      ResearchOSConversationController.fromApiClient(apiClient: widget.apiClient);

  @override
  void dispose() {
    _conversation.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final routes = const ResearchOSWorkspaceRoutes();
    final route = routes.forWorkspace(widget.workspace);
    final registry = const ResearchOSCapabilityRegistry();

    if (!registry.canAccess(widget.level, route.capability)) {
      return _V5AccessBoundary(route: route);
    }

    if (widget.workspace == ResearchOSWorkspace.friend) {
      return FriendWorkspace(
        apiClient: widget.apiClient,
        conversation: _conversation,
      );
    }

    final custom = widget.childBuilder;
    if (custom != null) return custom(context, route);

    return _V5MigrationBoundary(route: route);
  }
}

class _V5AccessBoundary extends StatelessWidget {
  const _V5AccessBoundary({required this.route});

  final ResearchOSWorkspaceRoute route;

  @override
  Widget build(BuildContext context) => Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 520),
          child: Card(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: <Widget>[
                  const Icon(Icons.lock_outline, size: 42),
                  const SizedBox(height: 12),
                  Text(
                    'ยังไม่มีสิทธิ์เข้า ${route.label}',
                    style: Theme.of(context).textTheme.titleLarge,
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'V5 จะไม่ข้าม capability หรือ authority boundary เพื่อเปิด workspace นี้',
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
            ),
          ),
        ),
      );
}

class _V5MigrationBoundary extends StatelessWidget {
  const _V5MigrationBoundary({required this.route});

  final ResearchOSWorkspaceRoute route;

  @override
  Widget build(BuildContext context) => Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 620),
          child: Card(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: <Widget>[
                  Icon(route.icon, size: 42),
                  const SizedBox(height: 12),
                  Text(
                    '${route.label} Workspace',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Semantic V5 route is ready. The existing feature remains the compatibility implementation until its workspace migration is validated.',
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
            ),
          ),
        ),
      );
}
