import 'package:flutter/material.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
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
          isAnalyzing: data['isAnalyzing'] ?? false,
          isDeleted: data['isDeleted'] ?? false,
          analysisResult: data['analysisResult'] != null 
              ? ScanResult.fromJson(Map<String, dynamic>.from(data['analysisResult'])) 
              : null,
        );
      }).toList();
    });
  }

  /// Sends a message and triggers the AI analysis flow
  Future<void> sendMessage(String chatId, String content, String type, {String? fileUrl}) async {
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
      'isAnalyzing': true,
      'isDeleted': false,
    });

    // 2. Perform AI Analysis (Mock or Real)
    try {
      final result = await _apiService.analyzeContent(type, content, fileUrl: fileUrl);
      
      // 3. Update Firestore document with result
      await docRef.update({
        'isAnalyzing': false,
        'analysisResult': result.toJson(),
      });

      // 4. Handle "FAKE" verdict for explosion
      if (result.verdict == 'FAKE') {
        // Wait for explosion animation to show on both devices
        await Future.delayed(const Duration(milliseconds: 2500));
        await docRef.update({'isDeleted': true});
      }
    } catch (e) {
      await docRef.update({'isAnalyzing': false});
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
