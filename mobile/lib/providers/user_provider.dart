import 'package:flutter/material.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';

class UserProvider extends ChangeNotifier {
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;
  final FirebaseAuth _auth = FirebaseAuth.instance;

  Map<String, dynamic>? _userData;
  Map<String, dynamic>? get userData => _userData;

  bool _isLoading = true;
  bool get isLoading => _isLoading;

  UserProvider() {
    _initUserListener();
  }

  void _initUserListener() {
    final user = _auth.currentUser;
    if (user != null) {
      _firestore.collection('users').doc(user.uid).snapshots().listen((snapshot) {
        if (snapshot.exists) {
          _userData = snapshot.data();
          _isLoading = false;
          notifyListeners();
        }
      });
    }
  }

  Future<void> updateOnlineStatus(bool isOnline) async {
    final user = _auth.currentUser;
    if (user == null) return;

    await _firestore.collection('users').doc(user.uid).update({
      'status': isOnline ? 'online' : 'offline',
      'lastSeen': FieldValue.serverTimestamp(),
    });
  }

  Future<void> updateProfile({String? displayName, String? about}) async {
    final user = _auth.currentUser;
    if (user == null) return;

    final updates = <String, dynamic>{};
    if (displayName != null) updates['displayName'] = displayName;
    if (about != null) updates['about'] = about;

    if (updates.isNotEmpty) {
      await _firestore.collection('users').doc(user.uid).update(updates);
    }
  }
}
