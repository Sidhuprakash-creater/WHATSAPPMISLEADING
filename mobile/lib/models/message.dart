// Data models for the MisLEADING app
// Updated to support the rich explanation engine

class Signal {
  final String label;
  final double prob;

  Signal({required this.label, required this.prob});

  factory Signal.fromJson(Map<String, dynamic> json) {
    return Signal(
      label: json['label'] ?? '',
      prob: (json['prob'] as num?)?.toDouble() ?? 0.0,
    );
  }
}

// ── Rich Explanation Models ───────────────────────────────────────────────

class RichEntity {
  final String name;
  final String type; // politician, businessman, celebrity, institution
  final String role;
  final String? partyOrCompany;
  final String? detailedBackground;
  final String? whyMentioned;
  final String? misuseNote;
  final String? wikipediaSummary;

  RichEntity({
    required this.name,
    required this.type,
    required this.role,
    this.partyOrCompany,
    this.detailedBackground,
    this.whyMentioned,
    this.misuseNote,
    this.wikipediaSummary,
  });

  factory RichEntity.fromJson(Map<String, dynamic> json) {
    return RichEntity(
      name: json['name'] ?? '',
      type: json['type'] ?? 'unknown',
      role: json['role'] ?? '',
      partyOrCompany: json['politics_business_context'] ?? json['party_or_company'] ?? json['party'],
      detailedBackground: json['background'] ?? json['detailed_background'],
      whyMentioned: json['why_mentioned'],
      misuseNote: json['misuse_note'],
      wikipediaSummary: json['wikipedia_summary'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'name': name,
      'type': type,
      'role': role,
      'politics_business_context': partyOrCompany,
      'background': detailedBackground,
      'why_mentioned': whyMentioned,
      'misuse_note': misuseNote,
      'wikipedia_summary': wikipediaSummary,
    };
  }
}

class ClaimVsReality {
  final String claim;
  final String reality;
  final String? sourceHint;

  ClaimVsReality({
    required this.claim,
    required this.reality,
    this.sourceHint,
  });

  factory ClaimVsReality.fromJson(Map<String, dynamic> json) {
    return ClaimVsReality(
      claim: json['claim'] ?? '',
      reality: json['reality'] ?? '',
      sourceHint: json['source_hint'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'claim': claim,
      'reality': reality,
      'source_hint': sourceHint,
    };
  }
}

class VerifiedSource {
  final String title;
  final String url;

  VerifiedSource({required this.title, required this.url});

  factory VerifiedSource.fromJson(Map<String, dynamic> json) {
    return VerifiedSource(
      title: json['title'] ?? json['url'] ?? '',
      url: json['url'] ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'title': title,
      'url': url,
    };
  }
}

class PatternFound {
  final String type;
  final String evidence;

  PatternFound({required this.type, required this.evidence});

  factory PatternFound.fromJson(dynamic json) {
    if (json is String) {
      return PatternFound(type: 'Pattern', evidence: json);
    }
    final map = json as Map<String, dynamic>;
    return PatternFound(
      type: (map['type'] ?? 'Pattern').toString().replaceAll('_', ' '),
      evidence: map['evidence'] ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'type': type,
      'evidence': evidence,
    };
  }
}

class RichExplanation {
  final String summary;
  final String primaryClaim;
  final List<String> whyFake;
  final List<RichEntity> entities;
  final List<ClaimVsReality> claimVsReality;
  final List<PatternFound> patternsFound;
  final String realVsFakeData;   // Web-synthesized real-time truth
  final List<VerifiedSource> verifiedSources;
  final bool safeToForward;
  final bool isAIGenerated;
  final bool isNSFW;
  final String mediaScanDetails;         // CvT-13 / Gemini forensic summary
  final List<String> manipulationSigns;  // Specific forensic findings

  RichExplanation({
    required this.summary,
    required this.primaryClaim,
    required this.whyFake,
    required this.entities,
    required this.claimVsReality,
    required this.patternsFound,
    required this.realVsFakeData,
    required this.verifiedSources,
    required this.safeToForward,
    this.isAIGenerated = false,
    this.isNSFW = false,
    this.mediaScanDetails = '',
    this.manipulationSigns = const [],
  });

  factory RichExplanation.fromJson(Map<String, dynamic> json) {
    // Extract manipulation_signs from nested media_scan_analysis
    List<String> signs = [];
    final mediaScanAnalysis = json['media_scan_analysis'];
    if (mediaScanAnalysis is Map<String, dynamic>) {
      final rawSigns = mediaScanAnalysis['manipulation_signs'];
      if (rawSigns is List) {
        signs = rawSigns.map((e) => e.toString()).toList();
      }
    }

    return RichExplanation(
      summary: json['summary'] ?? '',
      primaryClaim: json['primary_claim'] ?? '',
      whyFake: List<String>.from(json['why_fake'] ?? []),
      entities: (json['entities'] as List<dynamic>? ?? [])
          .map((e) => RichEntity.fromJson(e as Map<String, dynamic>))
          .toList(),
      claimVsReality: (json['claim_vs_reality'] as List<dynamic>? ?? [])
          .map((e) => ClaimVsReality.fromJson(e as Map<String, dynamic>))
          .toList(),
      patternsFound: (json['patterns_found'] as List<dynamic>? ?? [])
          .map((e) => PatternFound.fromJson(e is Map ? e as Map<String, dynamic> : {'type': 'pattern', 'evidence': e.toString()}))
          .toList(),
      realVsFakeData: json['real_vs_fake_data'] ?? '',
      verifiedSources: (json['verified_sources'] as List<dynamic>? ?? [])
          .map((e) => VerifiedSource.fromJson(e as Map<String, dynamic>))
          .toList(),
      safeToForward: json['safe_to_forward'] ?? true,
      isAIGenerated: json['is_ai_generated'] ?? false,
      isNSFW: json['is_nsfw'] ?? false,
      mediaScanDetails: json['media_scan_details'] ?? '',
      manipulationSigns: signs,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'summary': summary,
      'primary_claim': primaryClaim,
      'why_fake': whyFake,
      'entities': entities.map((e) => e.toJson()).toList(),
      'claim_vs_reality': claimVsReality.map((e) => e.toJson()).toList(),
      'patterns_found': patternsFound.map((e) => e.toJson()).toList(),
      'real_vs_fake_data': realVsFakeData,
      'verified_sources': verifiedSources.map((e) => e.toJson()).toList(),
      'safe_to_forward': safeToForward,
      'is_ai_generated': isAIGenerated,
      'is_nsfw': isNSFW,
      'media_scan_details': mediaScanDetails,
      'media_scan_analysis': {'manipulation_signs': manipulationSigns},
    };
  }

  bool get isEmpty =>
      summary.isEmpty && primaryClaim.isEmpty && whyFake.isEmpty && entities.isEmpty;
}

// ── Main Scan Result Model ────────────────────────────────────────────────

class ScanResult {
  final String id;
  final String verdict;
  final int confidence;
  final int riskScore;
  final List<String> reasons;
  final RichExplanation? explanation;
  final Map<String, dynamic> signals;
  final String? remoteUrl;

  ScanResult({
    required this.id,
    required this.verdict,
    required this.confidence,
    required this.riskScore,
    required this.reasons,
    this.explanation,
    required this.signals,
    this.remoteUrl,
  });


  factory ScanResult.fromJson(Map<String, dynamic> json) {
    return ScanResult(
      id: json['id'] ?? '',
      verdict: json['verdict'] ?? 'Low Risk',
      confidence: (json['confidence'] as num?)?.toInt() ?? 0,
      riskScore: (json['risk_score'] as num?)?.toInt() ?? 0,
      reasons: List<String>.from(json['reasons'] ?? []),
      explanation: json['explanation'] != null
          ? RichExplanation.fromJson(json['explanation'] as Map<String, dynamic>)
          : null,
      signals: json['signals'] ?? {},
      remoteUrl: json['remote_url'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'verdict': verdict,
      'confidence': confidence,
      'risk_score': riskScore,
      'reasons': reasons,
      'explanation': explanation?.toJson(),
      'signals': signals,
      'remote_url': remoteUrl,
    };
  }
}

// ── Chat Message Model ────────────────────────────────────────────────────

class Message {
  final String id;
  final String chatId;
  final String content;
  final String type; // text, url, image, video
  final bool isMe;
  final DateTime timestamp;
  final bool isForwarded;

  bool isAnalyzing;
  bool isDeleted;
  String? deletionReason;
  ScanResult? analysisResult;

  Message({
    required this.id,
    required this.chatId,
    required this.content,
    required this.type,
    required this.isMe,
    required this.timestamp,
    this.isForwarded = false,
    this.isAnalyzing = false,
    this.isDeleted = false,
    this.deletionReason,
    this.analysisResult,
  });
}
