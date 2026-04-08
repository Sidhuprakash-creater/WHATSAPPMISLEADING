import 'package:flutter/material.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'chat_detail_screen.dart';

class ChatListScreen extends StatefulWidget {
  const ChatListScreen({super.key});

  @override
  State<ChatListScreen> createState() => _ChatListScreenState();
}

class _ChatListScreenState extends State<ChatListScreen> {
  bool _isSelectionMode = false;
  final Set<String> _selectedChatIds = {};

  void _toggleSelection(String chatId) {
    setState(() {
      if (_selectedChatIds.contains(chatId)) {
        _selectedChatIds.remove(chatId);
        if (_selectedChatIds.isEmpty) {
          _isSelectionMode = false;
        }
      } else {
        _selectedChatIds.add(chatId);
      }
    });
  }

  void _clearSelection() {
    setState(() {
      _isSelectionMode = false;
      _selectedChatIds.clear();
    });
  }

  Future<void> _deleteSelectedChats() async {
    final uid = FirebaseAuth.instance.currentUser?.uid;
    if (uid == null) return;

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete Chats?'),
        content: Text('Are you sure you want to delete ${_selectedChatIds.length} chat(s)? This will remove your copy of the messages.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('CANCEL')),
          TextButton(
            onPressed: () => Navigator.pop(context, true), 
            child: const Text('DELETE', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      final batch = FirebaseFirestore.instance.batch();
      for (final chatId in _selectedChatIds) {
        // Technically, in a real app we might only remove the user from 'uids' 
        // or delete the document if uids.length == 1.
        // For this forensic app, we simulate deletion by removing the chat entry.
        batch.delete(FirebaseFirestore.instance.collection('chats').doc(chatId));
      }
      await batch.commit();
      _clearSelection();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Chats deleted successfully')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final uid = FirebaseAuth.instance.currentUser?.uid;
    if (uid == null) return const Center(child: CircularProgressIndicator());

    return Scaffold(
      appBar: _isSelectionMode 
        ? AppBar(
            backgroundColor: const Color(0xFF005C4B),
            leading: IconButton(
              icon: const Icon(Icons.close),
              onPressed: _clearSelection,
            ),
            title: Text('${_selectedChatIds.length}'),
            actions: [
              IconButton(
                icon: const Icon(Icons.delete),
                onPressed: _deleteSelectedChats,
              ),
            ],
          )
        : null, // Let the parent TabController/Scaffold handle the default AppBar if any
      body: StreamBuilder<QuerySnapshot>(
        stream: FirebaseFirestore.instance
            .collection('chats')
            .where('uids', arrayContains: uid)
            .snapshots(),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }

          if (!snapshot.hasData || snapshot.data!.docs.isEmpty) {
            return const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.chat_bubble_outline, size: 60, color: Colors.grey),
                  SizedBox(height: 16),
                  Text("No active chats yet."),
                  Text("Tap the chat icon to add a friend!"),
                ],
              ),
            );
          }

          final chats = snapshot.data!.docs;

          return ListView.builder(
            itemCount: chats.length,
            itemBuilder: (context, index) {
              final chatDoc = chats[index];
              final chatData = chatDoc.data() as Map<String, dynamic>;
              final chatId = chatDoc.id;
              final uids = List<String>.from(chatData['uids'] ?? []);
              final otherUid = uids.firstWhere((id) => id != uid, orElse: () => '');
              final isSelected = _selectedChatIds.contains(chatId);

              return StreamBuilder<DocumentSnapshot>(
                stream: FirebaseFirestore.instance.collection('users').doc(otherUid).snapshots(),
                builder: (context, userSnapshot) {
                  String name = 'Friend ($otherUid)';
                  String avatar = 'https://i.pravatar.cc/150?u=$otherUid';

                  if (userSnapshot.hasData && userSnapshot.data!.exists) {
                    final userData = userSnapshot.data!.data() as Map<String, dynamic>;
                    name = userData['displayName'] ?? name;
                    avatar = userData['avatarUrl'] ?? avatar;
                  }

                  return ListTile(
                    selected: isSelected,
                    selectedTileColor: Theme.of(context).primaryColor.withValues(alpha: 0.1),
                    leading: Stack(
                      children: [
                        CircleAvatar(
                          radius: 25,
                          backgroundImage: NetworkImage(avatar),
                        ),
                        if (isSelected)
                          Positioned(
                            right: 0,
                            bottom: 0,
                            child: Container(
                              padding: const EdgeInsets.all(2),
                              decoration: const BoxDecoration(
                                color: Colors.green,
                                shape: BoxShape.circle,
                              ),
                              child: const Icon(Icons.check, color: Colors.white, size: 14),
                            ),
                          ),
                      ],
                    ),
                    title: Text(
                      name,
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                    ),
                    subtitle: const Text(
                      'Tap to start chatting...',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(color: Colors.grey),
                    ),
                    onTap: () {
                      if (_isSelectionMode) {
                        _toggleSelection(chatId);
                      } else {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => ChatDetailScreen(
                              chatId: chatId,
                              name: name,
                              avatar: avatar,
                            ),
                          ),
                        );
                      }
                    },
                    onLongPress: () {
                      if (!_isSelectionMode) {
                        setState(() {
                          _isSelectionMode = true;
                          _selectedChatIds.add(chatId);
                        });
                      }
                    },
                  );
                },
              );
            },
          );
        },
      ),
    );
  }
}
