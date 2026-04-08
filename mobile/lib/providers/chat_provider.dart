import 'package:flutter/material.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'dart:io';
import '../models/message.dart';
import '../services/api_service.dart';

class ChatProvider extends ChangeNotifier {
  final ApiService _apiService = ApiService();
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;
  final FirebaseAuth _auth = FirebaseAuth.instance;

  /// Returns a live stream of messages for a specific chat ID
  Stream<List<Message>> getMessageStream(String chatId) {
    return _firestore
        .collection('chats')
        .doc(chatId)
        .collection('messages')
        .orderBy('timestamp', descending: true)
        .snapshots()
        .map((snapshot) {
      return snapshot.docs.map((doc) {
        final data = doc.data();
        final senderId = data['senderId'] as String;
        final currentUid = _auth.currentUser?.uid;
        
        return Message(
          id: doc.id,
          chatId: chatId,
          content: data['content'] ?? '',
          type: data['type'] ?? 'text',
          isMe: senderId == currentUid,
          timestamp: (data['timestamp'] as Timestamp?)?.toDate() ?? DateTime.now(),
          isForwarded: data['isForwarded'] ?? false,
          isAnalyzing: data['isAnalyzing'] ?? false,
          isDeleted: data['isDeleted'] ?? false,
          deletionReason: data['deletionReason'] as String?,
          analysisResult: data['analysisResult'] != null 
              ? ScanResult.fromJson(Map<String, dynamic>.from(data['analysisResult'])) 
              : null,
        );
      }).toList();
    });
  }

  /// Sends a message and triggers the AI analysis flow
  Future<void> sendMessage(String chatId, String content, String type, {String? fileUrl, bool isForwarded = false}) async {
    final uid = _auth.currentUser?.uid;
    if (uid == null) return;

    // 1. Add message to Firestore
    final docRef = await _firestore
        .collection('chats')
        .doc(chatId)
        .collection('messages')
        .add({
      'senderId': uid,
      'content': content,
      'type': type,
      'timestamp': FieldValue.serverTimestamp(),
      'isForwarded': isForwarded,
      'isAnalyzing': true,
      'isDeleted': false,
    });

    // 2. Perform AI Analysis (Real-time with Parallelization & Expanded explanation)
    try {
      final result = await _apiService.analyzeContent(
        contentType: type,
        textContent: (type == 'text' || type == 'url') ? content : null,
        file: (type == 'image' || type == 'document') ? File(content) : null, // content is path for files
      );
      
      // 3. Update Firestore document with result
      Map<String, dynamic> updates = {
        'isAnalyzing': false,
        'analysisResult': result.toJson(),
      };
      
      // If the backend hosted the file (cross-user sync), update content
      if (result.remoteUrl != null) {
        updates['content'] = result.remoteUrl;
        debugPrint('ChatProvider: Syncing remote URL to content: ${result.remoteUrl}');
      }
      
      await docRef.update(updates);

      
      // 4. AUTO-DELETE logic (RE-ENABLED)
      // Automatically delete messages that are flagged as high risk, fake or highly misleading
      final verdict = result.verdict.toUpperCase();
      final isHighlyRisky = verdict.contains('HIGH') || 
                            verdict.contains('FAKE') || 
                            verdict.contains('MISLEADING');
                            
      // Also auto-delete if the backend REJECTED it for safety (Error result with safety reason)
      final isSafetyViolation = result.verdict == 'Error' && 
                                result.reasons.any((r) => r.contains('Safety') || r.contains('Offensive'));

      final isImage = type == 'image';

      if ((isHighlyRisky || isSafetyViolation) && !isImage) {
        await deleteMessage(chatId, docRef.id);
        
        // Update deletion reason for transparency
        final reason = isSafetyViolation 
            ? 'Auto-deleted due to violation of safety standards (Detected aggressive or offensive content).'
            : 'Auto-deleted due to high misinformation risk or malicious content identified by CvT-13 AI.';
            
        await docRef.update({'deletionReason': reason});
        debugPrint('ChatProvider: Message auto-deleted due to ${isSafetyViolation ? "Safety Violation" : "High Risk"}.');
      }
    } catch (e) {
      debugPrint('ChatProvider: Critical analysis crash: $e');
      await docRef.update({'isAnalyzing': false});
    }
  }

  /// Deletes a message from Firestore
  Future<void> deleteMessage(String chatId, String messageId) async {
    await _firestore
        .collection('chats')
        .doc(chatId)
        .collection('messages')
        .doc(messageId)
        .update({'isDeleted': true});
  }

  /// Edits a message in Firestore
  Future<void> editMessage(String chatId, String messageId, String newContent) async {
    await _firestore
        .collection('chats')
        .doc(chatId)
        .collection('messages')
        .doc(messageId)
        .update({
      'content': newContent,
      'isAnalyzing': true, // Re-analyze edited content
    });
    
    // Optionally trigger re-analysis here if needed, 
    // but the backend logic for analysis usually happens on message creation. 
    // For now, just updating the content.
  }

  /// Forwards a message to multiple chats
  Future<void> forwardMessage(Message message, List<String> targetChatIds) async {
    for (String targetChatId in targetChatIds) {
      await sendMessage(targetChatId, message.content, message.type, isForwarded: true);
    }
  }

  /// Helper to start a chat between two users
  Future<String> getOrCreateChatId(String otherUid) async {
    final currentUid = _auth.currentUser?.uid;
    if (currentUid == null) throw Exception("Not logged in");

    // Unique ID based on alphabetical order of UIDs
    final List<String> ids = [currentUid, otherUid];
    ids.sort();
    final chatId = ids.join('_');

    final chatDoc = _firestore.collection('chats').doc(chatId);
    final exists = (await chatDoc.get()).exists;

    if (!exists) {
      await chatDoc.set({
        'uids': ids,
        'createdAt': FieldValue.serverTimestamp(),
        'lastMessage': null,
      });
    }
    
    return chatId;
  }
}
