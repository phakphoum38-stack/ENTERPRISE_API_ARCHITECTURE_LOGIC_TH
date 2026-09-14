import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_flutter/src/ui_v5/v5_capability.dart';
import 'package:research_os_flutter/src/ui_v5/v5_workspace_route.dart';

void main() {
  const registry = ResearchOSCapabilityRegistry();
  const routes = ResearchOSWorkspaceRoutes();

  test('capabilities inherit by user level', () {
    expect(
      registry.canAccess(
        ResearchOSUserLevel.user,
        ResearchOSCapability.friend,
      ),
      isTrue,
    );
    expect(
      registry.canAccess(
        ResearchOSUserLevel.user,
        ResearchOSCapability.github,
      ),
      isFalse,
    );
    expect(
      registry.canAccess(
        ResearchOSUserLevel.developer,
        ResearchOSCapability.github,
      ),
      isTrue,
    );
    expect(
      registry.canAccess(
        ResearchOSUserLevel.owner,
        ResearchOSCapability.evidence,
      ),
      isTrue,
    );
    expect(
      registry.canAccess(
        ResearchOSUserLevel.owner,
        ResearchOSCapability.ownerSpecial,
      ),
      isFalse,
    );
    expect(
      registry.canAccess(
        ResearchOSUserLevel.ownerSpecial,
        ResearchOSCapability.ownerSpecial,
      ),
      isTrue,
    );
  });

  test('workspace routes use stable semantic identities', () {
    expect(routes.forRoute('friend').workspace, ResearchOSWorkspace.friend);
    expect(routes.forRoute('developer').workspace, ResearchOSWorkspace.developer);
    expect(routes.forRoute('evidence').workspace, ResearchOSWorkspace.evidence);
    expect(routes.forRoute('owner').workspace, ResearchOSWorkspace.owner);
  });

  test('basic user only sees non-privileged workspaces', () {
    final visible = routes.visibleFor(ResearchOSUserLevel.user);
    final ids = visible.map((item) => item.route).toSet();

    expect(ids, containsAll(<String>{'friend', 'research', 'memory', 'library', 'settings'}));
    expect(ids, isNot(contains('developer')));
    expect(ids, isNot(contains('owner')));
    expect(ids, isNot(contains('evidence')));
  });

  test('developer sees engineering workspace but not owner workspace', () {
    final visible = routes.visibleFor(ResearchOSUserLevel.developer);
    final ids = visible.map((item) => item.route).toSet();

    expect(ids, contains('developer'));
    expect(ids, contains('brain'));
    expect(ids, contains('factory'));
    expect(ids, isNot(contains('owner')));
  });

  test('owner special inherits owner and privileged capability', () {
    final visible = registry.capabilitiesFor(ResearchOSUserLevel.ownerSpecial);

    expect(visible, contains(ResearchOSCapability.owner));
    expect(visible, contains(ResearchOSCapability.evidence));
    expect(visible, contains(ResearchOSCapability.ownerSpecial));
  });
}
