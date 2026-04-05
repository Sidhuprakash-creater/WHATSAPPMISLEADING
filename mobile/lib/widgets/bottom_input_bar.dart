import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:image_picker/image_picker.dart';
import 'package:file_picker/file_picker.dart';
import '../providers/chat_provider.dart';

class BottomInputBar extends StatefulWidget {
  final String chatId;
  
  const BottomInputBar({super.key, required this.chatId});

  @override
  State<BottomInputBar> createState() => _BottomInputBarState();
}

class _BottomInputBarState extends State<BottomInputBar> {
  final TextEditingController _controller = TextEditingController();
  bool _isTyping = false;
  final ImagePicker _picker = ImagePicker();

  void _showComingSoon(BuildContext context, String feature) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('\$feature coming soon!'),
        duration: const Duration(seconds: 1),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  Future<void> _pickImage() async {
    try {
      final XFile? image = await _picker.pickImage(source: ImageSource.camera);
      if (image != null && mounted) {
        Provider.of<ChatProvider>(context, listen: false)
            .sendMessage(widget.chatId, '📷 Image Attached', 'image', fileUrl: image.path);
      }
    } catch (e) {
      if (mounted) _showComingSoon(context, "Camera Access (Emulator limitation)");
    }
  }

  Future<void> _pickFile() async {
    try {
      FilePickerResult? result = await FilePicker.pickFiles();
      if (result != null && mounted) {
        Provider.of<ChatProvider>(context, listen: false)
            .sendMessage(widget.chatId, '📄 Document Attached', 'document');
      }
    } catch (e) {
      if (mounted) _showComingSoon(context, "File Access");
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 8.0),
      color: Colors.transparent,
      child: Row(
        children: [
          Expanded(
            child: Container(
              decoration: BoxDecoration(
                color: Theme.of(context).brightness == Brightness.dark 
                    ? const Color(0xFF202C33) 
                    : Colors.white,
                borderRadius: BorderRadius.circular(24.0),
              ),
              child: Row(
                children: [
                  IconButton(
                    icon: const Icon(Icons.emoji_emotions_outlined, color: Colors.grey),
                    onPressed: () => _showComingSoon(context, "Emoji Keyboard"),
                  ),
                  Expanded(
                    child: TextField(
                      controller: _controller,
                      onChanged: (val) {
                        setState(() {
                          _isTyping = val.isNotEmpty;
                        });
                      },
                      decoration: const InputDecoration(
                        hintText: 'Message',
                        hintStyle: TextStyle(color: Colors.grey),
                        border: InputBorder.none,
                      ),
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.attach_file, color: Colors.grey),
                    onPressed: _pickFile,
                  ),
                  if (!_isTyping)
                    IconButton(
                      icon: const Icon(Icons.camera_alt, color: Colors.grey),
                      onPressed: _pickImage,
                    ),
                ],
              ),
            ),
          ),
          const SizedBox(width: 8),
          CircleAvatar(
            radius: 24,
            backgroundColor: const Color(0xFF00A884),
            child: IconButton(
              icon: Icon(
                _isTyping ? Icons.send : Icons.mic,
                color: Colors.white,
              ),
              onPressed: () {
                if (_isTyping) {
                  final text = _controller.text;
                  _controller.clear();
                  setState(() {
                    _isTyping = false;
                  });
                  Provider.of<ChatProvider>(context, listen: false)
                      .sendMessage(widget.chatId, text, 'text');
                } else {
                  _showComingSoon(context, "Voice Message");
                }
              },
            ),
          ),
        ],
      ),
    );
  }
}
