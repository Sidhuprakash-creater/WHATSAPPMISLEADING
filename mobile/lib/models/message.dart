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

  Map<String, dynamic> toJson() {
    return {
      'label': label,
      'prob': prob,
    };
  }
}

class ScanResult {
  final String id;
  final String verdict; // SAFE, MISLEADING, FAKE
  final int confidence;
  final int riskScore;
  final List<String> reasons;
  final Map<String, dynamic> signals; // raw signals

  ScanResult({
    required this.id,
    required this.verdict,
    required this.confidence,
    required this.riskScore,
    required this.reasons,
    required this.signals,
  });

  factory ScanResult.fromJson(Map<String, dynamic> json) {
    return ScanResult(
      id: json['id'] ?? '',
      verdict: json['verdict'] ?? 'SAFE',
      confidence: json['confidence'] ?? 0,
      riskScore: json['risk_score'] ?? 0,
      reasons: List<String>.from(json['reasons'] ?? []),
      signals: json['signals'] ?? {},
    );
  }

  Map<String, dynamic> toJson() {
    return {'id': id, 'verdict': verdict, 'confidence': confidence, 'risk_score': riskScore, 'reasons': reasons, 'signals': signals};
  }
}

class Message {
  final String id;
  final String chatId;
  final String content; // Text, URL, or local path for media
  final String type; // text, url, image, video, document
  final bool isMe;
  final DateTime timestamp;

  bool isAnalyzing;
  bool isDeleted;
  ScanResult? analysisResult;

  Message({
    required this.id,
    required this.chatId,
    required this.content,
    required this.type,
    required this.isMe,
    required this.timestamp,
    this.isAnalyzing = false,
    this.isDeleted = false,
    this.analysisResult,
  });
}
