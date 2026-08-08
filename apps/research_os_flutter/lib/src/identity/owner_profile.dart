class OwnerProfile {
  const OwnerProfile({
    required this.email,
    required this.updatedAt,
  });

  final String email;
  final DateTime updatedAt;

  String get displayLabel => email;

  OwnerProfile copyWith({String? email, DateTime? updatedAt}) {
    return OwnerProfile(
      email: email ?? this.email,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }
}
