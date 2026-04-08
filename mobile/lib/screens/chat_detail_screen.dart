import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import '../providers/chat_provider.dart';
import '../models/message.dart';
import '../widgets/bottom_input_bar.dart';
import '../widgets/message_bubble.dart';
import 'package:flutter/services.dart';

class ChatDetailScreen extends StatefulWidget {
  final String chatId;
  final String name;
  final String avatar;

  const ChatDetailScreen({
    super.key, 
    required this.chatId,
    required this.name, 
    required this.avatar
  });

  @override
  State<ChatDetailScreen> createState() => _ChatDetailScreenState();
}

class _ChatDetailScreenState extends State<ChatDetailScreen> {
  bool _isSearching = false;
  final TextEditingController _searchController = TextEditingController();
  String _searchQuery = '';

  bool _isSelectionMode = false;
  final List<String> _selectedMessageIds = [];
  List<Message> _currentMessages = [];

  void _toggleSelection(String messageId) {
    setState(() {
      if (_selectedMessageIds.contains(messageId)) {
        _selectedMessageIds.remove(messageId);
        if (_selectedMessageIds.isEmpty) {
          _isSelectionMode = false;
        }
      } else {
        _selectedMessageIds.add(messageId);
      }
    });
  }

  void _clearSelection() {
    setState(() {
      _isSelectionMode = false;
      _selectedMessageIds.clear();
    });
  }

  void _showBatchForwardDialog(BuildContext context) {
    if (_selectedMessageIds.isEmpty) return;
    
    final uid = FirebaseAuth.instance.currentUser?.uid;
    final Set<String> targetChatIds = {};

    showDialog(
      context: context,
      builder: (dialogContext) => StatefulBuilder(
        builder: (context, setDialogState) {
          return AlertDialog(
            title: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(child: Text('Forward ${_selectedMessageIds.length} message(s)')),
                if (targetChatIds.isNotEmpty)
                  TextButton(
                    onPressed: () => setDialogState(() => targetChatIds.clear()),
                    child: const Text('Clear', style: TextStyle(fontSize: 12)),
                  ),
              ],
            ),
            content: SizedBox(
              width: double.maxFinite,
              height: 400,
              child: StreamBuilder<QuerySnapshot>(
                stream: FirebaseFirestore.instance
                    .collection('chats')
                    .where('uids', arrayContains: uid)
                    .snapshots(),
                builder: (context, snapshot) {
                  if (!snapshot.hasData) return const Center(child: CircularProgressIndicator());
                  final chats = snapshot.data!.docs;
                  
                  return Column(
                    children: [
                      CheckboxListTile(
                        title: const Text("Select All Chats", style: TextStyle(fontWeight: FontWeight.bold)),
                        value: targetChatIds.length == chats.length && chats.isNotEmpty,
                        onChanged: (val) {
                          setDialogState(() {
                            if (val == true) {
                              targetChatIds.addAll(chats.map((c) => c.id));
                            } else {
                              targetChatIds.clear();
                            }
                          });
                        },
                      ),
                      const Divider(),
                      Expanded(
                        child: ListView.builder(
                          shrinkWrap: true,
                          itemCount: chats.length,
                          itemBuilder: (context, index) {
                            final chatId = chats[index].id;
                            final isSelected = targetChatIds.contains(chatId);
                            final uids = List<String>.from((chats[index].data() as Map<String, dynamic>)['uids'] ?? []);
                            final otherUid = uids.firstWhere((id) => id != uid, orElse: () => '');

                            return StreamBuilder<DocumentSnapshot>(
                              stream: FirebaseFirestore.instance.collection('users').doc(otherUid).snapshots(),
                              builder: (context, userSnap) {
                                if (!userSnap.hasData || !userSnap.data!.exists) return const SizedBox();
                                final name = (userSnap.data!.data() as Map<String, dynamic>)['displayName'] ?? 'Friend';
                                return CheckboxListTile(
                                  secondary: const Icon(Icons.account_circle, color: Colors.blueAccent),
                                  title: Text(name),
                                  value: isSelected,
                                  onChanged: (val) {
                                    setDialogState(() {
                                      if (val == true) {
                                        targetChatIds.add(chatId);
                                      } else {
                                        targetChatIds.remove(chatId);
                                      }
                                    });
                                  },
                                );
                              },
                            );
                          },
                        ),
                      ),
                    ],
                  );
                },
              ),
            ),
            actions: [
              TextButton(onPressed: () => Navigator.pop(dialogContext), child: const Text('CANCEL')),
              ElevatedButton(
                onPressed: targetChatIds.isEmpty ? null : () {
                  final chatProvider = Provider.of<ChatProvider>(context, listen: false);
                  final selectedMsgs = _currentMessages.where((m) => _selectedMessageIds.contains(m.id)).toList();
                  
                  for (final msg in selectedMsgs) {
                    chatProvider.forwardMessage(msg, targetChatIds.toList());
                  }
                  
                  Navigator.pop(dialogContext);
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Forwarded to ${targetChatIds.length} chat(s)')),
                  );
                  _clearSelection();
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF005C4B),
                  foregroundColor: Colors.white,
                ),
                child: const Text('FORWARD'),
              ),
            ],
          );
        }
      ),
    );
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final chatProvider = Provider.of<ChatProvider>(context, listen: false);

    return Scaffold(
      backgroundColor: Theme.of(context).brightness == Brightness.dark 
          ? const Color(0xFF0B141A) 
          : const Color(0xFFEFE7DD), 
      appBar: _isSelectionMode 
        ? AppBar(
            backgroundColor: const Color(0xFF005C4B),
            leading: IconButton(
              icon: const Icon(Icons.close),
              onPressed: _clearSelection,
            ),
            title: Text('${_selectedMessageIds.length}'),
            actions: [
              IconButton(
                icon: const Icon(Icons.select_all),
                onPressed: () {
                  setState(() {
                    _selectedMessageIds.clear();
                    _selectedMessageIds.addAll(_currentMessages.map((m) => m.id));
                  });
                },
              ),
              IconButton(
                icon: const Icon(Icons.copy),
                onPressed: () {
                  final textToCopy = _currentMessages
                      .where((m) => _selectedMessageIds.contains(m.id))
                      .map((m) => m.content)
                      .join("\n\n");
                  Clipboard.setData(ClipboardData(text: textToCopy));
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Messages copied')));
                  _clearSelection();
                },
              ),
              IconButton(
                icon: const Icon(Icons.forward),
                onPressed: () => _showBatchForwardDialog(context),
              ),
              IconButton(
                icon: const Icon(Icons.delete),
                onPressed: () {
                  for (final id in _selectedMessageIds) {
                    chatProvider.deleteMessage(widget.chatId, id);
                  }
                  _clearSelection();
                },
              ),
            ],
          )
        : AppBar(
            titleSpacing: 0,
        leadingWidth: 70,
        leading: InkWell(
          onTap: () {
            if (_isSearching) {
              setState(() {
                _isSearching = false;
                _searchQuery = '';
                _searchController.clear();
              });
            } else {
              Navigator.pop(context);
            }
          },
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.arrow_back, size: 24),
              const SizedBox(width: 4),
              CircleAvatar(radius: 18, backgroundImage: NetworkImage(widget.avatar)),
            ],
          ),
        ),
        title: _isSearching 
          ? TextField(
              controller: _searchController,
              autofocus: true,
              style: const TextStyle(color: Colors.white, fontSize: 18),
              decoration: const InputDecoration(
                hintText: 'Search messages...',
                hintStyle: TextStyle(color: Colors.white60),
                border: InputBorder.none,
              ),
              onChanged: (val) {
                setState(() {
                  _searchQuery = val.toLowerCase();
                });
              },
            )
          : StreamBuilder<DocumentSnapshot>(
              stream: FirebaseFirestore.instance.collection('chats').doc(widget.chatId).snapshots(),
              builder: (context, chatSnap) {
                String currentName = widget.name;
                if (chatSnap.hasData && chatSnap.data!.exists) {
                   final uids = List<String>.from((chatSnap.data!.data() as Map<String, dynamic>)['uids'] ?? []);
                   final otherUid = uids.firstWhere((u) => u != FirebaseAuth.instance.currentUser?.uid, orElse: () => '');
                   return StreamBuilder<DocumentSnapshot>(
                     stream: FirebaseFirestore.instance.collection('users').doc(otherUid).snapshots(),
                     builder: (context, userSnap) {
                       String status = 'offline';
                       if (userSnap.hasData && userSnap.data!.exists) {
                         final userData = userSnap.data!.data() as Map<String, dynamic>;
                         currentName = userData['displayName'] ?? widget.name;
                         status = userData['status'] ?? 'offline';
                       }
                       return Column(
                         crossAxisAlignment: CrossAxisAlignment.start,
                         children: [
                           Text(currentName, style: const TextStyle(fontSize: 18.5, fontWeight: FontWeight.bold)),
                           Text(
                             status, 
                             style: TextStyle(
                               fontSize: 13, 
                               color: status == 'online' ? Colors.greenAccent : Colors.grey
                             )
                           ),
                         ],
                       );
                     },
                   );
                }
                return Text(widget.name);
              },
            ),
        actions: [
          IconButton(
            onPressed: () {
              setState(() {
                _isSearching = !_isSearching;
                if (!_isSearching) {
                  _searchQuery = '';
                  _searchController.clear();
                }
              });
            }, 
            icon: Icon(_isSearching ? Icons.close : Icons.search)
          ),
          IconButton(onPressed: () {}, icon: const Icon(Icons.videocam)),
          IconButton(onPressed: () {}, icon: const Icon(Icons.call)),
          IconButton(onPressed: () {}, icon: const Icon(Icons.more_vert)),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: StreamBuilder<List<Message>>(
              stream: chatProvider.getMessageStream(widget.chatId),
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.waiting) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (!snapshot.hasData || snapshot.data!.isEmpty) {
                  return const Center(child: Text("Say hi! No messages yet."));
                }
                
                final messages = snapshot.data!.where((m) {
                  if (_searchQuery.isEmpty) return true;
                  return m.content.toLowerCase().contains(_searchQuery);
                }).toList();

                // Silently update the reference for "Select All" functionality
                WidgetsBinding.instance.addPostFrameCallback((_) {
                  if (mounted) _currentMessages = messages;
                });

                if (messages.isEmpty && _searchQuery.isNotEmpty) {
                  return const Center(child: Text("No matches found."));
                }

                return ListView.builder(
                  reverse: true,
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 15),
                  itemCount: messages.length,
                  itemBuilder: (context, index) {
                    final msg = messages[index];
                    return MessageBubble(
                      message: msg,
                      isSelected: _selectedMessageIds.contains(msg.id),
                      isSelectionMode: _isSelectionMode,
                      onTap: _isSelectionMode ? () => _toggleSelection(msg.id) : null,
                      onLongPress: () {
                        if (!_isSelectionMode) {
                          setState(() {
                            _isSelectionMode = true;
                            _selectedMessageIds.add(msg.id);
                          });
                        } else {
                          _toggleSelection(msg.id);
                        }
                      },
                    );
                  },
                );
              },
            ),
          ),
          BottomInputBar(chatId: widget.chatId),
        ],
      ),
    );
  }
}
