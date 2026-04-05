import 'package:flutter/material.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'chat_detail_screen.dart';

class ChatListScreen extends StatelessWidget {
  const ChatListScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final uid = FirebaseAuth.instance.currentUser?.uid;
    if (uid == null) return const Center(child: CircularProgressIndicator());

    return StreamBuilder<QuerySnapshot>(
      // Listen to all chats where the current user's UID is in the 'uids' array
      stream: FirebaseFirestore.instance
          .collection('chats')
          .where('uids', arrayContains: uid)
          .snapshots(),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }

        if (!snapshot.hasData || snapshot.data!.docs.isEmpty) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.chat_bubble_outline, size: 60, color: Colors.grey),
                const SizedBox(height: 16),
                const Text("No active chats yet."),
                const Text("Tap the chat icon to add a friend!"),
              ],
            ),
          );
        }

        final chats = snapshot.data!.docs;

        return ListView.builder(
          itemCount: chats.length,
          itemBuilder: (context, index) {
            final chat = chats[index].data() as Map<String, dynamic>;
            final chatId = chats[index].id;
            
            // Assume the other user is the one that isn't me
            final uids = List<String>.from(chat['uids'] ?? []);
            final otherUid = uids.firstWhere((id) => id != uid, orElse: () => 'System');

            return ListTile(
              leading: const CircleAvatar(
                radius: 25,
                backgroundImage: NetworkImage('https://i.pravatar.cc/150?u=temp'),
              ),
              title: Text(
                'Friend ($otherUid)', // For now showing the UID suffix
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
              ),
              subtitle: const Text(
                'Tap to start chatting...',
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(color: Colors.grey),
              ),
              trailing: const Text(
                'now',
                style: TextStyle(color: Colors.grey, fontSize: 12),
              ),
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => ChatDetailScreen(
                      chatId: chatId,
                      name: 'Friend ($otherUid)',
                      avatar: 'https://i.pravatar.cc/150?u=$otherUid',
                    ),
                  ),
                );
              },
            );
          },
        );
      },
    );
  }
}
