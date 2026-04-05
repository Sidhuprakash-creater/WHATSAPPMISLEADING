import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'chat_list_screen.dart';
import 'add_friend_screen.dart';
import 'profile_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  String _myId = 'Loading...';

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this, initialIndex: 1);
    _loadMyId();
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
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('WhatsApp', style: TextStyle(fontWeight: FontWeight.w500)),
        actions: [
          IconButton(onPressed: () {}, icon: const Icon(Icons.camera_alt_outlined)),
          IconButton(onPressed: () {}, icon: const Icon(Icons.search)),
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
}
