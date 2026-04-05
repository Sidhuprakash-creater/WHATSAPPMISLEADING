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

  Future<void> updateProfile({String? displayName, String? status}) async {
    final user = _auth.currentUser;
    if (user == null) return;

    final updates = <String, dynamic>{};
    if (displayName != null) updates['displayName'] = displayName;
    if (status != null) updates['status'] = status;

    if (updates.isNotEmpty) {
      await _firestore.collection('users').doc(user.uid).update(updates);
    }
  }
}
