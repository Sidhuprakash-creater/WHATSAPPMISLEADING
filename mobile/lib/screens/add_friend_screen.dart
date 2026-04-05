import 'package:flutter/material.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:provider/provider.dart';
import '../providers/chat_provider.dart';
import 'chat_detail_screen.dart';
import 'qr_scanner_screen.dart';

class AddFriendScreen extends StatefulWidget {
  const AddFriendScreen({super.key});

  @override
  State<AddFriendScreen> createState() => _AddFriendScreenState();
}

class _AddFriendScreenState extends State<AddFriendScreen> {
  final TextEditingController _idController = TextEditingController();
  bool _isSearching = false;

  Future<void> _searchAndAddFriend() async {
    final entry = _idController.text.trim();
    if (entry.isEmpty) return;

    final chatProvider = context.read<ChatProvider>();
    final messenger = ScaffoldMessenger.of(context);
    final navigator = Navigator.of(context);

    setState(() => _isSearching = true);

    try {
      // Find user with that shareable ID
      final query = await FirebaseFirestore.instance
          .collection('users')
          .where('shortId', isEqualTo: entry)
          .limit(1)
          .get();

      if (query.docs.isEmpty) {
        messenger.showSnackBar(
          const SnackBar(content: Text("User ID not found! Check and try again.")),
        );
      } else {
        final otherUid = query.docs.first.id;
        final name = query.docs.first.data()['displayName'] ?? 'Friend';
        
        final chatId = await chatProvider.getOrCreateChatId(otherUid);

        navigator.pushReplacement(
          MaterialPageRoute(
            builder: (context) => ChatDetailScreen(
              chatId: chatId, 
              name: name, 
              avatar: 'https://i.pravatar.cc/150?u=$otherUid'
            ),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
           SnackBar(content: Text("Error: \$e")),
        );
      }
    } finally {
      if (mounted) setState(() => _isSearching = false);
    }
  }

  Future<void> _openScanner() async {
    final result = await Navigator.push(
      context,
      MaterialPageRoute(builder: (context) => const QrScannerScreen()),
    );

    if (result != null && result is String) {
      _idController.text = result;
      _searchAndAddFriend();
    }
  }

  @override
  void dispose() {
    _idController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("New Chat")),
      body: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              "Enter your friend's MisLEADING ID to start chatting!",
              style: TextStyle(fontSize: 16, color: Colors.grey),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 30),
            TextField(
              controller: _idController,
              decoration: InputDecoration(
                hintText: "e.g. SAFETY_9824",
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                prefixIcon: const Icon(Icons.person_add),
              ),
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: _isSearching ? null : _searchAndAddFriend,
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 15),
                backgroundColor: const Color(0xFF00A884),
              ),
              child: _isSearching 
                  ? const CircularProgressIndicator(color: Colors.white) 
                  : const Text("Add Friend", style: TextStyle(fontSize: 18)),
            ),
            const SizedBox(height: 20),
            const Center(child: Text("OR", style: TextStyle(color: Colors.grey))),
            const SizedBox(height: 20),
            OutlinedButton.icon(
              onPressed: _openScanner,
              icon: const Icon(Icons.qr_code_scanner, color: Color(0xFF00A884)),
              label: const Text("Scan QR Code", style: TextStyle(color: Color(0xFF00A884))),
              style: OutlinedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 15),
                side: const BorderSide(color: Color(0xFF00A884)),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
