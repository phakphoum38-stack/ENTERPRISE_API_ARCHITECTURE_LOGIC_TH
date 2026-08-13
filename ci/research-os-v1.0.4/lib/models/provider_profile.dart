class ProviderProfile {
  const ProviderProfile({
    required this.id,
    required this.name,
    required this.baseUrl,
    required this.model,
    required this.enabled,
    this.apiStyle = 'openai-compatible',
    this.keyStored = false,
  });

  final String id;
  final String name;
  final String baseUrl;
  final String model;
  final bool enabled;
  final String apiStyle;
  final bool keyStored;

  ProviderProfile copyWith({
    String? id,
    String? name,
    String? baseUrl,
    String? model,
    bool? enabled,
    String? apiStyle,
    bool? keyStored,
  }) {
    return ProviderProfile(
      id: id ?? this.id,
      name: name ?? this.name,
      baseUrl: baseUrl ?? this.baseUrl,
      model: model ?? this.model,
      enabled: enabled ?? this.enabled,
      apiStyle: apiStyle ?? this.apiStyle,
      keyStored: keyStored ?? this.keyStored,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'baseUrl': baseUrl,
        'model': model,
        'enabled': enabled,
        'apiStyle': apiStyle,
      };

  factory ProviderProfile.fromJson(Map<String, dynamic> json) {
    return ProviderProfile(
      id: '${json['id'] ?? ''}',
      name: '${json['name'] ?? 'Provider'}',
      baseUrl: '${json['baseUrl'] ?? ''}',
      model: '${json['model'] ?? ''}',
      enabled: json['enabled'] == true,
      apiStyle: '${json['apiStyle'] ?? 'openai-compatible'}',
    );
  }
}
