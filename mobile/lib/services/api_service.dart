import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../models/message.dart';

class ApiService {
  // Using your local IP for real device testing
  static const String baseUrl = 'http://10.49.240.11:8000/api/v1';
  static bool useMock = false; // Enabled real backend analysis!

  Future<ScanResult> analyzeContent(String contentType, String textContent, {String? fileUrl}) async {
    if (useMock) {
      await Future.delayed(const Duration(seconds: 2));
      return _getMockResult(contentType, textContent);
    }

    try {
      String? finalFilePayload = fileUrl;
      
      // If it's a local file path (not an HTTP URL), convert to Base64
      if (fileUrl != null && !fileUrl.startsWith('http')) {
        final file = File(fileUrl);
        if (await file.exists()) {
          final bytes = await file.readAsBytes();
          final base64String = base64Encode(bytes);
          final extension = file.path.split('.').last.toLowerCase();
          final mimeType = (extension == 'png') ? 'image/png' : 'image/jpeg';
          finalFilePayload = 'data:$mimeType;base64,$base64String';
        }
      }

      final response = await http.post(
        Uri.parse('$baseUrl/analyze'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'content_type': contentType,
          'text': (contentType == 'text' || contentType == 'url') ? textContent : null,
          'file_url': finalFilePayload,
        }),
      );

      if (response.statusCode == 200) {
        return ScanResult.fromJson(jsonDecode(response.body));
      } else {
        throw Exception('Failed to analyze content: ${response.statusCode}');
      }
    } catch (e) {
      debugPrint('API Error: $e');
      // Fallback to mock on connection error to keep UI functional during dev
      return _getMockResult(contentType, textContent);
    }
  }

  ScanResult _getMockResult(String contentType, String textContent) {
    String verdict = 'SAFE';
    int riskScore = 15;
    List<String> reasons = [];

    final textLower = textContent.toLowerCase();

    // Simple mock logic for demonstration
    if (textLower.contains('fake') || textLower.contains('urgent') || textLower.contains('forward this')) {
      verdict = 'FAKE';
      riskScore = 85;
      reasons = [
        'Detected common panic-inducing terminology ("urgent", "forward this").',
        'Unable to verify the claims from authoritative sources.',
        'High probability of being a trending rumor based on historical ML data.'
      ];
    } else if (textLower.contains('free') || textLower.contains('win') || textLower.contains('prize')) {
      verdict = 'FAKE';
      riskScore = 95;
      reasons = [
        'Matches known phishing scam patterns.',
        'Uses typical baiting techniques ("free", "win").',
        'VirusTotal reports domain as malicious.'
      ];
    } else if (textLower.contains('claim') || textLower.contains('rumor')) {
      verdict = 'MISLEADING';
      riskScore = 45;
      reasons = [
        'The statement lacks context or presents a half-truth.',
        'Further fact-checking required before believing this claim.'
      ];
    }

    return ScanResult(
      id: 'mock-${DateTime.now().millisecondsSinceEpoch}',
      verdict: verdict,
      confidence: 90,
      riskScore: riskScore,
      reasons: reasons,
      signals: {'ml_probability': riskScore / 100.0},
    );
  }
}
