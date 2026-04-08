import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:image_picker/image_picker.dart';
import 'chat_list_screen.dart';
import 'add_friend_screen.dart';
import 'profile_screen.dart';
import 'chat_detail_screen.dart';
import '../providers/user_provider.dart';
import 'package:provider/provider.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> with SingleTickerProviderStateMixin, WidgetsBindingObserver {
  late TabController _tabController;
  String _myId = 'Loading...';

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _tabController = TabController(length: 4, vsync: this, initialIndex: 1);
    _loadMyId();
    _setOnline(true);
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      _setOnline(true);
    } else {
      _setOnline(false);
    }
  }

  void _setOnline(bool isOnline) {
    Provider.of<UserProvider>(context, listen: false).updateOnlineStatus(isOnline);
  }

  void _loadMyId() {
    final user = FirebaseAuth.instance.currentUser;
    if (user != null) {
      // Use the last 4 chars of the UID as a short ID
      setState(() {
        _myId = 'SAFETY_${user.uid.substring(user.uid.length - 4).toUpperCase()}';
      });
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _setOnline(false);
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('WhatsApp', style: TextStyle(fontWeight: FontWeight.w500)),
        actions: [
          IconButton(onPressed: _handleCamera, icon: const Icon(Icons.camera_alt_outlined)),
          IconButton(
            onPressed: () {
              showSearch(
                context: context,
                delegate: ChatSearchDelegate(
                  onChatSelected: (chatId, name, avatar) {
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
                  },
                ),
              );
            }, 
            icon: const Icon(Icons.search)
          ),
          IconButton(onPressed: () {
            Navigator.push(
              context,
              MaterialPageRoute(builder: (context) => const ProfileScreen()),
            );
          }, icon: const Icon(Icons.person_outline)),
          PopupMenuButton<String>(
            onSelected: (value) {
              if (value == 'profile') {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => const ProfileScreen()),
                );
              }
            },
            itemBuilder: (context) => [
              const PopupMenuItem(value: 'profile', child: Text('Profile')),
              const PopupMenuItem(value: 'settings', child: Text('Settings')),
            ],
          ),
        ],
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(icon: Icon(Icons.groups)),
            Tab(text: 'Chats'),
            Tab(text: 'Updates'),
            Tab(text: 'Calls'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: const [
          Center(child: Text('Communities')),
          ChatListScreen(),
          Center(child: Text('Updates')),
          Center(child: Text('Calls')),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          Navigator.push(
            context,
            MaterialPageRoute(builder: (context) => const AddFriendScreen()),
          );
        },
        child: const Icon(Icons.chat),
      ),
      // Overlay the My ID badge subtly
      bottomNavigationBar: Container(
        height: 20,
        color: const Color(0xFF202C33),
        child: Center(
          child: Text(
            "Your ID: $_myId", 
            style: const TextStyle(fontSize: 10, color: Colors.grey),
          ),
        ),
      ),
    );
  }

  Future<void> _handleCamera() async {
    final ImagePicker picker = ImagePicker();
    final XFile? photo = await picker.pickImage(source: ImageSource.camera);
    if (photo != null && mounted) {
      // Prompt user where to send this image
      showDialog(
        context: context,
        builder: (ctx) => AlertDialog(
          title: const Text('Send Photo'),
          content: const Text('Choose a contact to send this photo to, or post to Status.'),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Cancel'),
            ),
            TextButton(
              onPressed: () {
                Navigator.pop(ctx);
                _tabController.animateTo(1); // Go to Chats tab
              },
              child: const Text('Select Contact'),
            ),
          ],
        ),
      );
    }
  }
}

class ChatSearchDelegate extends SearchDelegate {
  final Function(String, String, String) onChatSelected;

  ChatSearchDelegate({required this.onChatSelected});

  @override
  List<Widget>? buildActions(BuildContext context) {
    return [
      IconButton(
        icon: const Icon(Icons.clear),
        onPressed: () => query = '',
      ),
    ];
  }

  @override
  Widget? buildLeading(BuildContext context) {
    return IconButton(
      icon: const Icon(Icons.arrow_back),
      onPressed: () => close(context, null),
    );
  }

  @override
  Widget buildResults(BuildContext context) {
    return _buildSearchResults(context);
  }

  @override
  Widget buildSuggestions(BuildContext context) {
    return _buildSearchResults(context);
  }

  Widget _buildSearchResults(BuildContext context) {
    final uid = FirebaseAuth.instance.currentUser?.uid;
    return StreamBuilder<QuerySnapshot>(
      stream: FirebaseFirestore.instance.collection('chats').where('uids', arrayContains: uid).snapshots(),
      builder: (context, snapshot) {
        if (!snapshot.hasData) return const Center(child: CircularProgressIndicator());
        
        final chatDocs = snapshot.data!.docs;

        return ListView.builder(
          itemCount: chatDocs.length,
          itemBuilder: (context, index) {
            final chatData = chatDocs[index].data() as Map<String, dynamic>;
            final chatId = chatDocs[index].id;
            final uids = List<String>.from(chatData['uids'] ?? []);
            final otherUid = uids.firstWhere((id) => id != uid, orElse: () => '');

            return FutureBuilder<DocumentSnapshot>(
              future: FirebaseFirestore.instance.collection('users').doc(otherUid).get(),
              builder: (context, userSnap) {
                if (!userSnap.hasData || !userSnap.data!.exists) return const SizedBox.shrink();
                final userData = userSnap.data!.data() as Map<String, dynamic>;
                final name = userData['displayName'] ?? 'Friend';
                final avatar = userData['avatarUrl'] ?? 'https://i.pravatar.cc/150?u=$otherUid';

                bool matches = name.toLowerCase().contains(query.toLowerCase());
                if (query.isNotEmpty && !matches) return const SizedBox.shrink();

                return ListTile(
                  leading: CircleAvatar(backgroundImage: NetworkImage(avatar)),
                  title: Text(name),
                  onTap: () {
                    close(context, null);
                    onChatSelected(chatId, name, avatar);
                  },
                );
              },
            );
          },
        );
      },
    );
  }
}
