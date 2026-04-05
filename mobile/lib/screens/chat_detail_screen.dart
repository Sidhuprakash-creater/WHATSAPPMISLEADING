import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/chat_provider.dart';
import '../models/message.dart';
import '../widgets/bottom_input_bar.dart';
import '../widgets/message_bubble.dart';

class ChatDetailScreen extends StatelessWidget {
  final String chatId;
  final String name;
  final String avatar;

  const ChatDetailScreen({
    super.key, 
    required this.chatId,
    required this.name, 
    required this.avatar
  });

  void _showComingSoon(BuildContext context, String feature) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('\$feature feature coming soon!'),
        duration: const Duration(seconds: 1),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final chatProvider = Provider.of<ChatProvider>(context, listen: false);

    return Scaffold(
      backgroundColor: Theme.of(context).brightness == Brightness.dark 
          ? const Color(0xFF0B141A) 
          : const Color(0xFFEFE7DD), 
      appBar: AppBar(
        titleSpacing: 0,
        leadingWidth: 70,
        leading: InkWell(
          onTap: () => Navigator.pop(context),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.arrow_back, size: 24),
              CircleAvatar(radius: 16, backgroundImage: NetworkImage(avatar)),
            ],
          ),
        ),
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(name, style: const TextStyle(fontSize: 18.5, fontWeight: FontWeight.bold)),
            const Text('online', style: TextStyle(fontSize: 13)),
          ],
        ),
        actions: [
          IconButton(onPressed: () => _showComingSoon(context, "Video Call"), icon: const Icon(Icons.videocam)),
          IconButton(onPressed: () => _showComingSoon(context, "Audio Call"), icon: const Icon(Icons.call)),
          IconButton(onPressed: () => _showComingSoon(context, "Settings"), icon: const Icon(Icons.more_vert)),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: StreamBuilder<List<Message>>(
              stream: chatProvider.getMessageStream(chatId),
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.waiting) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (!snapshot.hasData || snapshot.data!.isEmpty) {
                  return const Center(child: Text("Say hi! No messages yet."));
                }
                
                final messages = snapshot.data!;
                return ListView.builder(
                  reverse: true,
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 15),
                  itemCount: messages.length,
                  itemBuilder: (context, index) => MessageBubble(message: messages[index]),
                );
              },
            ),
          ),
          BottomInputBar(chatId: chatId),
        ],
      ),
    );
  }
}
