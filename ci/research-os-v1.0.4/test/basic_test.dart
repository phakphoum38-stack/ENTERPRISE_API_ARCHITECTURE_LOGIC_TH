import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_control_center/models/app_settings.dart';
import 'package:research_os_control_center/models/provider_profile.dart';

void main() {
  test('AppSettings round trip', () {
    const settings = AppSettings(githubOwner: 'owner', autoRefreshSeconds: 30, autoSync: false, preferredRootPath: r'G:\My Drive\DRIVE_VIRTUAL_CLOUD');
    final restored = AppSettings.fromJson(settings.toJson());
    expect(restored.githubOwner, 'owner');
    expect(restored.autoRefreshSeconds, 30);
    expect(restored.autoSync, false);
  });

  test('ProviderProfile round trip excludes secret', () {
    const profile = ProviderProfile(id: 'p1', name: 'Local', baseUrl: 'http://localhost:8000/v1', model: 'm1', enabled: true);
    final json = profile.toJson();
    expect(json.containsKey('apiKey'), false);
    expect(ProviderProfile.fromJson(json).model, 'm1');
  });
}
