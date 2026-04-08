import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:path/path.dart' as path;
import '../models/message.dart';

class ApiService {
  final String baseUrl = 'http://127.0.0.1:8000'; // Replace with your backend URL

  Future<ScanResult> analyzeContent({
    required String contentType,
    String? textContent,
    File? file,
  }) async {
    try {
      String? finalFilePayload;

      if (file != null) {
        if (contentType == 'image' || contentType == 'document') {
          List<int> fileBytes = await file.readAsBytes();
          String base64String = base64Encode(fileBytes);
          String extension = path.extension(file.path).replaceAll('.', '').toLowerCase();
          
          String mimeType = 'application/octet-stream';
          if (extension == 'png') {
            mimeType = 'image/png';
          } else if (extension == 'jpg' || extension == 'jpeg') {
            mimeType = 'image/jpeg';
          } else if (extension == 'pdf') {
            mimeType = 'application/pdf';
          } else if (extension == 'apk') {
            mimeType = 'application/vnd.android.package-archive';
          }

          finalFilePayload = 'data:$mimeType;base64,$base64String';
        }
      }

      debugPrint('ApiService: Sending $contentType request to $baseUrl/analyze...');
      
      final response = await http.post(
        Uri.parse('$baseUrl/analyze'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'content_type': contentType,
          'text': (contentType == 'text' || contentType == 'url') ? textContent : null,
          'file_url': finalFilePayload,
          'client_platform': 'mobile_app',
        }),
      ).timeout(const Duration(seconds: 150)); // Support complex multi-model analysis (150s)

      if (response.statusCode == 200) {
        debugPrint('ApiService: Success (200)');
        return ScanResult.fromJson(jsonDecode(response.body));
      } else {
        String serverMsg = 'The AI engine returned an error (${response.statusCode}).';
        try {
          final errorBody = jsonDecode(response.body);
          if (errorBody is Map && errorBody.containsKey('detail')) {
            serverMsg = errorBody['detail'];
          }
        } catch (_) {
          // Fallback to generic if JSON is invalid
        }
        
        final errorMsg = 'Server Error ${response.statusCode}: $serverMsg';
        debugPrint('ApiService: $errorMsg');
        return _getErrorResult(serverMsg);
      }
    } on SocketException catch (e) {
      debugPrint('ApiService: Connection Failed — $e');
      return _getErrorResult(
          'Could not connect to the server. Please check if your backend is running.');
    } on http.ClientException catch (e) {
       debugPrint('ApiService: HTTP Client Exception — $e');
       return _getErrorResult('Network error. Please check your internet connection.');
    } catch (e) {
      debugPrint('ApiService: Unexpected Error — $e');
      return _getErrorResult('An unexpected error occurred. Please try again.');
    }
  }

  ScanResult _getErrorResult(String message) {
    return ScanResult(
      id: 'error_${DateTime.now().millisecondsSinceEpoch}',
      verdict: 'Error',
      confidence: 0,
      riskScore: 0,
      reasons: [message],
      signals: {},
    );
  }
}
