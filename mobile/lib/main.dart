import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:cloud_firestore/cloud_firestore.dart';

import 'providers/chat_provider.dart';
import 'providers/user_provider.dart';
import 'screens/home_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const LoadingApp());
}

class LoadingApp extends StatefulWidget {
  const LoadingApp({super.key});

  @override
  State<LoadingApp> createState() => _LoadingAppState();
}

class _LoadingAppState extends State<LoadingApp> {
  String _status = 'Initializing Firebase...';
  bool _hasError = false;

  @override
  void initState() {
    super.initState();
    _startSetup();
  }

  Future<void> _startSetup() async {
    try {
      if (Firebase.apps.isEmpty) {
        await Firebase.initializeApp();
      }

      setState(() => _status = 'Authenticating User...');
      final auth = FirebaseAuth.instance;
      if (auth.currentUser == null) {
        await auth.signInAnonymously();
      }

      setState(() => _status = 'Setting up Database...');
      final user = auth.currentUser!;
      final userDoc = FirebaseFirestore.instance.collection('users').doc(user.uid);
      final doc = await userDoc.get();

      if (!doc.exists) {
        final shortId = 'SAFETY_${user.uid.substring(user.uid.length - 4).toUpperCase()}';
        await userDoc.set({
          'uid': user.uid,
          'shortId': shortId,
          'displayName': 'SafetyUser_${user.uid.substring(user.uid.length - 2)}',
          'status': 'Hey there! I am using MisLEADING WhatsApp.',
          'lastSeen': FieldValue.serverTimestamp(),
        });
      }

      debugPrint('FIREBASE_SETUP_SUCCESS: Fully Connected!');
      
      runApp(
        MultiProvider(
          providers: [
            ChangeNotifierProvider(create: (_) => UserProvider()),
            ChangeNotifierProvider(create: (_) => ChatProvider()),
          ],
          child: const MyApp(),
        ),
      );
    } catch (e) {
      debugPrint('FIREBASE_SETUP_ERROR: $e');
      setState(() {
        _hasError = true;
        if (e.toString().contains('CONFIGURATION_NOT_FOUND')) {
          _status = 'ERROR: Anonymous Sign-in is NOT enabled in your Firebase Console!\n\nPlease go to Firebase Console -> Authentication -> Sign-in method -> Enable "Anonymous".';
        } else if (e.toString().contains('cloud_firestore/unavailable')) {
          _status = 'ERROR: Firestore Database Not Found!\n\nPlease go to Firebase Console -> Firestore Database -> Click "Create Database" (Start in Test Mode).';
        } else if (e.toString().contains('permission-denied')) {
          _status = 'ERROR: Database Permissions Denied!\n\nYou selected "Production Mode" instead of "Test Mode".\n\nGo to Firebase Console -> Firestore Database -> Rules tab.\nChange "allow read, write: if false;" to "allow read, write: if true;" and click Publish.';
        } else {
          _status = 'Setup Error: $e';
        }
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      home: Scaffold(
        backgroundColor: const Color(0xFF111B21),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                if (!_hasError) const CircularProgressIndicator(color: Color(0xFF00A884)),
                const SizedBox(height: 24),
                Text(
                  _status,
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    color: _hasError ? Colors.redAccent : Colors.white,
                    fontSize: 16,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'VeriBlast WhatsApp',
      debugShowCheckedModeBanner: false,
      themeMode: ThemeMode.dark,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF075E54)),
        primaryColor: const Color(0xFF075E54),
        scaffoldBackgroundColor: Colors.white,
      ),
      darkTheme: ThemeData(
        brightness: Brightness.dark,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF00A884),
          brightness: Brightness.dark,
        ),
        scaffoldBackgroundColor: const Color(0xFF111B21),
        primaryColor: const Color(0xFF00A884),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF202C33),
          foregroundColor: Colors.white,
          elevation: 0,
        ),
        // ... (other theme parts)
      ),
      home: const HomeScreen(),
    );
  }
}
