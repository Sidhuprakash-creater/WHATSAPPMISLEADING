import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:image_picker/image_picker.dart';
import 'package:file_picker/file_picker.dart';
import '../providers/chat_provider.dart';
import '../utils/profanity_filter.dart';

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
        content: Text('$feature coming soon!'),
        duration: const Duration(seconds: 1),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  Future<void> _pickImage(ImageSource source) async {
    try {
      final XFile? image = await _picker.pickImage(source: source);
      if (image != null && mounted) {
        // Show loading state while analyzing? For now just send
        Provider.of<ChatProvider>(context, listen: false)
            .sendMessage(widget.chatId, image.path, 'image', fileUrl: image.path);
      }
    } catch (e) {
      if (mounted) _showComingSoon(context, "Camera/Gallery Access");
    }
  }

  Future<void> _pickFile() async {
    try {
      FilePickerResult? result = await FilePicker.pickFiles();
      if (result != null && mounted) {
        final filePath = result.files.single.path;
        if (filePath != null) {
            Provider.of<ChatProvider>(context, listen: false)
                .sendMessage(widget.chatId, filePath, 'document', fileUrl: filePath);
        }
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
                        final badWord = ProfanityFilter.detectBadWord(val);
                        if (badWord != null) {
                          // Show warning SnackBar
                          ScaffoldMessenger.of(context).hideCurrentSnackBar();
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                              content: Text('⚠️ Warning: This word is not allowed!'),
                              backgroundColor: Colors.redAccent,
                              behavior: SnackBarBehavior.floating,
                              duration: Duration(seconds: 2),
                            ),
                          );
                          
                          // Clean text and restore cursor
                          final clean = ProfanityFilter.cleanText(val);
                          _controller.value = _controller.value.copyWith(
                            text: clean,
                            selection: TextSelection.collapsed(offset: clean.length),
                          );
                        }
                        
                        setState(() {
                          _isTyping = _controller.text.isNotEmpty;
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
                      onPressed: () async {
                        // Let user choose camera or gallery for flexibility
                        showModalBottomSheet(
                          context: context,
                          builder: (context) => SafeArea(
                            child: Wrap(
                              children: [
                                ListTile(
                                  leading: const Icon(Icons.camera_alt),
                                  title: const Text('Camera'),
                                  onTap: () { Navigator.pop(context); _pickImage(ImageSource.camera); },
                                ),
                                ListTile(
                                  leading: const Icon(Icons.photo_library),
                                  title: const Text('Gallery'),
                                  onTap: () { Navigator.pop(context); _pickImage(ImageSource.gallery); },
                                ),
                              ],
                            ),
                          ),
                        );
                      },
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
