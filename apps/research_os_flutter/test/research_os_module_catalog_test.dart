import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_flutter/src/ui/new_gui/research_os_module_catalog.dart';

void main() {
  test('new GUI catalog keeps module ids and labels unique', () {
    final ids = researchOSNewGuiModules.map((module) => module.id).toList();
    final labels = researchOSNewGuiModules.map((module) => module.label).toList();

    expect(ids.toSet().length, ids.length);
    expect(labels.toSet().length, labels.length);
  });

  test('new GUI catalog contains all required top-level destinations', () {
    final ids = researchOSNewGuiModules.map((module) => module.id).toSet();

    expect(
      ids,
      containsAll(<ResearchOSModuleId>{
        ResearchOSModuleId.home,
        ResearchOSModuleId.chat,
        ResearchOSModuleId.agents,
        ResearchOSModuleId.memory,
        ResearchOSModuleId.skills,
        ResearchOSModuleId.tools,
        ResearchOSModuleId.factory,
        ResearchOSModuleId.providers,
        ResearchOSModuleId.files,
        ResearchOSModuleId.repositories,
        ResearchOSModuleId.github,
        ResearchOSModuleId.drive,
        ResearchOSModuleId.runtime,
        ResearchOSModuleId.installer,
        ResearchOSModuleId.backup,
        ResearchOSModuleId.restore,
        ResearchOSModuleId.shell,
      }),
    );
  });

  test('classic destinations retain their legacy page adapters', () {
    const classicIds = <ResearchOSModuleId>{
      ResearchOSModuleId.home,
      ResearchOSModuleId.chat,
      ResearchOSModuleId.agents,
      ResearchOSModuleId.github,
      ResearchOSModuleId.drive,
      ResearchOSModuleId.runtime,
    };

    for (final id in classicIds) {
      final module = researchOSNewGuiModules.firstWhere((item) => item.id == id);
      expect(module.availability, 'existing');
      expect(
        module.legacyPageIndex,
        isNotNull,
        reason: '${module.label} must keep its classic page adapter',
      );
    }
  });

  test('newly wired modules have a real backend source without fake legacy index', () {
    const wiredIds = <ResearchOSModuleId>{
      ResearchOSModuleId.skills,
      ResearchOSModuleId.tools,
      ResearchOSModuleId.installer,
      ResearchOSModuleId.backup,
      ResearchOSModuleId.restore,
      ResearchOSModuleId.shell,
    };

    for (final id in wiredIds) {
      final module = researchOSNewGuiModules.firstWhere((item) => item.id == id);
      expect(module.availability, 'existing');
      expect(module.legacyPageIndex, isNull);
      expect(module.backendSource, isNotNull);
      expect(module.backendSource, isNotEmpty);
    }
  });

  test('planned modules never pretend to have a current page index', () {
    for (final module in researchOSNewGuiModules.where(
      (module) => module.availability == 'planned',
    )) {
      expect(module.legacyPageIndex, isNull);
      expect(module.backendSource, isNotNull);
    }
  });
}
