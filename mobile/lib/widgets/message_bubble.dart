import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import '../models/message.dart';
import '../providers/chat_provider.dart';
import 'package:flutter_linkify/flutter_linkify.dart';
import 'package:url_launcher/url_launcher.dart';
import 'dart:io';
import 'dart:ui';

class MessageBubble extends StatefulWidget {
  final Message message;
  final String? searchHighlight;
  final bool isSelected;
  final bool isSelectionMode;
  final VoidCallback? onTap;
  final VoidCallback? onLongPress;

  const MessageBubble({
    super.key, 
    required this.message, 
    this.searchHighlight,
    this.isSelected = false,
    this.isSelectionMode = false,
    this.onTap,
    this.onLongPress,
  });

  @override
  State<MessageBubble> createState() => _MessageBubbleState();
}

class _MessageBubbleState extends State<MessageBubble> {
  late bool _showAnalysis;
  bool _isNSFWUnveiled = false;

  @override
  void initState() {
    super.initState();
    final analysis = widget.message.analysisResult;
    final isImage = widget.message.type == 'image';
    
    bool isFake = false;
    if (analysis != null) {
      if (widget.message.type == 'image') {
        final verdict = analysis.verdict.toUpperCase();
        final isAIGenerated = analysis.explanation?.isAIGenerated ?? false;
        isFake = verdict.contains('HIGH') || verdict.contains('MEDIUM') || isAIGenerated || verdict.contains('FAKE') || verdict.contains('MISLEADING');
      } else {
        final verdict = analysis.verdict.toUpperCase();
        isFake = verdict.contains('HIGH') || verdict.contains('MEDIUM') || verdict.contains('FAKE') || verdict.contains('MISLEADING');
      }
    }
    _showAnalysis = (!widget.message.isMe && widget.message.isForwarded && isFake);
  }

  void _showActions(BuildContext context) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (context) => Container(
        padding: const EdgeInsets.symmetric(vertical: 20),
        decoration: BoxDecoration(
          color: Theme.of(context).cardColor,
          borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.copy, color: Colors.blue),
              title: const Text('Copy'),
              onTap: () {
                Clipboard.setData(ClipboardData(text: widget.message.content));
                Navigator.pop(context);
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Message copied')),
                );
              },
            ),
            ListTile(
              leading: const Icon(Icons.edit, color: Colors.blue),
              title: const Text('Edit Message'),
              onTap: () {
                Navigator.pop(context);
                _showEditDialog(context);
              },
            ),
            ListTile(
              leading: const Icon(Icons.forward, color: Colors.green),
              title: const Text('Forward'),
              onTap: () {
                Navigator.pop(context);
                _showForwardDialog(context);
              },
            ),
            ListTile(
              leading: const Icon(Icons.delete, color: Colors.red),
              title: const Text('Delete for Both'),
              onTap: () {
                Navigator.pop(context);
                context.read<ChatProvider>().deleteMessage(widget.message.chatId, widget.message.id);
              },
            ),
          ],
        ),
      ),
    );
  }

  void _showEditDialog(BuildContext context) {
    final controller = TextEditingController(text: widget.message.content);
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Edit Message'),
        content: TextField(
          controller: controller,
          decoration: const InputDecoration(hintText: 'Enter new content'),
          autofocus: true,
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          TextButton(
            onPressed: () {
              context.read<ChatProvider>().editMessage(widget.message.chatId, widget.message.id, controller.text);
              Navigator.pop(context);
            },
            child: const Text('Save'),
          ),
        ],
      ),
    );
  }

  void _showForwardDialog(BuildContext context) {
    final uid = FirebaseAuth.instance.currentUser?.uid;
    showDialog(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Forward message to:'),
        content: SizedBox(
          width: double.maxFinite,
          height: 300,
          child: StreamBuilder<QuerySnapshot>(
            stream: FirebaseFirestore.instance
                .collection('chats')
                .where('uids', arrayContains: uid)
                .snapshots(),
            builder: (context, snapshot) {
              if (!snapshot.hasData) return const Center(child: CircularProgressIndicator());
              final chats = snapshot.data!.docs;
              return ListView.builder(
                shrinkWrap: true,
                itemCount: chats.length,
                itemBuilder: (context, index) {
                  final chatId = chats[index].id;
                  final uids = List<String>.from((chats[index].data() as Map<String, dynamic>)['uids'] ?? []);
                  final otherUid = uids.firstWhere((id) => id != uid, orElse: () => '');

                  return StreamBuilder<DocumentSnapshot>(
                    stream: FirebaseFirestore.instance.collection('users').doc(otherUid).snapshots(),
                    builder: (context, userSnap) {
                      if (!userSnap.hasData || !userSnap.data!.exists) return const SizedBox();
                      final name = (userSnap.data!.data() as Map<String, dynamic>)['displayName'] ?? 'Friend';
                      return ListTile(
                        leading: const Icon(Icons.account_circle, color: Colors.blueAccent),
                        title: Text(name),
                        onTap: () {
                          Provider.of<ChatProvider>(dialogContext, listen: false)
                              .forwardMessage(widget.message, [chatId]);
                          Navigator.pop(dialogContext);
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(content: Text('Forwarded to $name')),
                          );
                        },
                      );
                    },
                  );
                },
              );
            },
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialogContext), child: const Text('Cancel')),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final message = widget.message;
    bool isDark = Theme.of(context).brightness == Brightness.dark;
    final selectionColor = isDark ? Colors.teal.withValues(alpha: 0.3) : Colors.green.withValues(alpha: 0.3);

    Color bubbleColor = message.isMe 
        ? (isDark ? const Color(0xFF005C4B) : const Color(0xFFD9FDD3))
        : (isDark ? const Color(0xFF202C33) : Colors.white);
    
    if (widget.isSelected) {
      bubbleColor = Color.alphaBlend(selectionColor, bubbleColor);
    }
        
    Color textColor = isDark ? Colors.white : Colors.black87;
    
    if (message.isDeleted) {
      return Align(
        alignment: message.isMe ? Alignment.centerRight : Alignment.centerLeft,
        child: Container(
          margin: const EdgeInsets.symmetric(vertical: 2.0),
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
          decoration: BoxDecoration(
            color: bubbleColor.withValues(alpha: 0.5),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.report_gmailerrorred, size: 14, color: isDark ? Colors.redAccent.withValues(alpha: 0.7) : Colors.red),
              const SizedBox(width: 6),
              Flexible(
                child: Text(
                  message.deletionReason != null 
                    ? "Deleted: ${message.deletionReason}" 
                    : "This message was deleted",
                  style: const TextStyle(fontSize: 13, fontStyle: FontStyle.italic, color: Colors.grey),
                ),
              ),
            ],
          ),
        ),
      );
    }

    final analysis = message.analysisResult;
    final verdict = analysis?.verdict.toUpperCase() ?? '';
    final isImage = message.type == 'image';
    final isUnknown = verdict.contains('UNKNOWN') || verdict.contains('ERROR');
    final isAIGenerated = analysis?.explanation?.isAIGenerated ?? false;
    
    final isFake = isImage 
      ? (verdict.contains('HIGH') || verdict.contains('MEDIUM') || isAIGenerated || verdict.contains('FAKE') || verdict.contains('MISLEADING'))
      : (verdict.contains('HIGH') || verdict.contains('MEDIUM') || verdict.contains('FAKE') || verdict.contains('MISLEADING'));
      
    final isMaliciousDocument = isFake && message.type == 'document';

    return GestureDetector(
      onLongPress: () {
        if (widget.onLongPress != null) {
          widget.onLongPress!();
        } else {
          _showActions(context);
        }
      },
      onTap: () {
        if (widget.isSelectionMode && widget.onTap != null) {
          widget.onTap!();
        } else if (analysis != null) {
          setState(() => _showAnalysis = !_showAnalysis);
        }
      },
      child: Column(
        crossAxisAlignment: message.isMe ? CrossAxisAlignment.end : CrossAxisAlignment.start,
        children: [
          Align(
            alignment: message.isMe ? Alignment.centerRight : Alignment.centerLeft,
            child: Container(
              margin: const EdgeInsets.symmetric(vertical: 2.0),
              constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.8),
              decoration: BoxDecoration(
                color: bubbleColor,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Stack(
                    children: [
                      Padding(
                        padding: const EdgeInsets.fromLTRB(10, 8, 48, 12),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            if (message.type == 'image')
                              _buildImageContent(context, message, isDark)
                            else
                              _buildContentWithHighlight(
                                message.content, 
                                widget.searchHighlight, 
                                textColor
                              ),
                            if (isAIGenerated) ...[
                              const SizedBox(height: 6),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
                                decoration: BoxDecoration(
                                  color: Colors.purple.withValues(alpha: 0.15),
                                  borderRadius: BorderRadius.circular(6),
                                  border: Border.all(color: Colors.purple.withValues(alpha: 0.4)),
                                ),
                                child: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    const Text('🤖', style: TextStyle(fontSize: 12)),
                                    const SizedBox(width: 4),
                                    Text('AI Generated Content', style: TextStyle(fontSize: 11, color: Colors.purple.shade300, fontWeight: FontWeight.bold)),
                                  ],
                                ),
                              ),
                            ],
                            if (isMaliciousDocument) ...[
                              const SizedBox(height: 6),
                               Container(
                                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
                                decoration: BoxDecoration(
                                  color: Colors.red.withValues(alpha: 0.15),
                                  borderRadius: BorderRadius.circular(6),
                                  border: Border.all(color: Colors.redAccent.withValues(alpha: 0.4)),
                                ),
                                child: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    const Icon(Icons.shield_rounded, size: 12, color: Colors.redAccent),
                                    const SizedBox(width: 4),
                                    Text('Forensic Alert: Do Not Open', style: TextStyle(fontSize: 11, color: Colors.redAccent, fontWeight: FontWeight.bold)),
                                  ],
                                ),
                              ),
                            ],
                            if (isFake && !_showAnalysis) ...[
                              const SizedBox(height: 6),
                              Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Icon(isImage ? Icons.image_search : Icons.warning_amber_rounded, size: 18, color: isImage ? Colors.purple : (isDark ? Colors.redAccent : Colors.red)),
                                  const SizedBox(width: 4),
                                  Text(isImage ? 'Tap to view CvT-13 Analysis' : 'Tap to view risk details', style: TextStyle(fontSize: 12, color: isImage ? Colors.purple : (isDark ? Colors.redAccent : Colors.red), fontStyle: FontStyle.italic)),
                                ],
                              ),
                            ],
                            if (!isFake && analysis != null && analysis.explanation?.safeToForward == true && message.content.contains('http')) ...[
                              const SizedBox(height: 6),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                decoration: BoxDecoration(
                                  color: Colors.green.withValues(alpha: 0.15),
                                  borderRadius: BorderRadius.circular(4),
                                  border: Border.all(color: Colors.green.withValues(alpha: 0.3)),
                                ),
                                child: const Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    Icon(Icons.verified_user, size: 12, color: Colors.green),
                                    SizedBox(width: 4),
                                    Text('Verified Safe Link', style: TextStyle(fontSize: 11, color: Colors.green, fontWeight: FontWeight.w600)),
                                  ],
                                ),
                              ),
                            ]
                          ],
                        ),
                      ),
                      Positioned(
                        bottom: 4,
                        right: 8,
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Text(
                              DateFormat('HH:mm').format(message.timestamp),
                              style: TextStyle(fontSize: 11, color: isDark ? Colors.white60 : Colors.black54),
                            ),
                            if (message.isMe) ...[
                              const SizedBox(width: 4),
                              const Icon(Icons.done_all, size: 16, color: Colors.blue),
                              if (message.isAnalyzing) ...[
                                const SizedBox(width: 4),
                                const SizedBox(
                                  width: 10,
                                  height: 10,
                                  child: CircularProgressIndicator(strokeWidth: 1.5, color: Colors.blueAccent),
                                ),
                              ],
                            ]
                          ],
                        ),
                      ),
                    ],
                  ),
                  
                  // BANNERS
                  if (isFake && !isImage) Builder(
                    builder: (context) {
                      final patterns = analysis?.explanation?.patternsFound ?? [];
                      final isScam = patterns.any((p) => 
                        p.type.toLowerCase().contains('scam') || 
                        p.type.toLowerCase().contains('phishing')
                      );
                      
                      return Container(
                        width: double.infinity,
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                        decoration: BoxDecoration(
                          color: isScam ? Colors.red.withValues(alpha: 0.2) : Colors.red.withValues(alpha: 0.12),
                          border: Border(top: BorderSide(color: Colors.red.withValues(alpha: 0.15))),
                        ),
                        child: Column(
                          children: [
                            Row(
                              children: [
                                Icon(
                                  isScam ? Icons.gpp_maybe_rounded : Icons.error_outline_rounded, 
                                  size: 18, 
                                  color: Colors.red
                                ),
                                const SizedBox(width: 8),
                                Expanded(
                                  child: Text(
                                    isScam ? '🚨 SCAM LINK DETECTED' : 'MISINFORMATION RISK',
                                    style: TextStyle(
                                      fontSize: 11,
                                      fontWeight: FontWeight.bold,
                                      color: Colors.red.shade900,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                            if (isScam) ...[
                              const SizedBox(height: 4),
                              Text(
                                'Warning: This link resembles a financial scam (KBC, Lottery, or Phishing). Do not click or share bank details.',
                                style: TextStyle(fontSize: 10, color: Colors.red.shade800),
                              ),
                              const SizedBox(height: 8),
                              Row(
                                mainAxisAlignment: MainAxisAlignment.end,
                                children: [
                                  TextButton.icon(
                                    onPressed: () {
                                      context.read<ChatProvider>().deleteMessage(widget.message.chatId, widget.message.id);
                                    },
                                    icon: const Icon(Icons.delete_forever, size: 14, color: Colors.red),
                                    label: const Text('Review & Delete', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Colors.red)),
                                  ),
                                ],
                              )
                            ] else ...[
                              const SizedBox(height: 2),
                              Text(
                                'This message may contain unverified info.',
                                style: TextStyle(fontSize: 10, color: Colors.red.shade800),
                              ),
                            ],
                          ],
                        ),
                      );
                    }
                  ),
                  
                  if (isUnknown) Builder(
                    builder: (context) => Container(
                      width: double.infinity,
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                      decoration: BoxDecoration(
                        color: Colors.orange.withValues(alpha: 0.12),
                        border: Border(top: BorderSide(color: Colors.orange.withValues(alpha: 0.15))),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.sync_problem_rounded, size: 16, color: Colors.orange),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              'ANALYSIS FAILED (TIMEOUT)',
                              style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Colors.orange.shade900),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  
                  if (_showAnalysis && analysis != null)
                    AnimatedContainer(
                      duration: const Duration(milliseconds: 300),
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: isImage && isFake 
                            ? Colors.purple.withValues(alpha: 0.08) 
                            : (isFake ? Colors.red.withValues(alpha: 0.08) : Colors.black.withValues(alpha: 0.05)),
                        borderRadius: const BorderRadius.vertical(bottom: Radius.circular(12)),
                        border: isFake 
                            ? Border(top: BorderSide(color: isImage ? Colors.purple.withValues(alpha: 0.2) : Colors.red.withValues(alpha: 0.2))) 
                            : null,
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          if (isFake && !isImage) ...[
                            Row(
                              children: [
                                Icon(Icons.warning_amber_rounded, size: 14, color: Colors.orange.shade800),
                                const SizedBox(width: 6),
                                Text(
                                  'RISK ANALYSIS',
                                  style: TextStyle(
                                    fontSize: 11,
                                    fontWeight: FontWeight.bold,
                                    letterSpacing: 0.5,
                                    color: Colors.red.shade900,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 8),
                          ],
                          
                          if (analysis.explanation != null) ...[
                            if (!isImage)
                              Text(
                                analysis.explanation!.summary,
                                style: TextStyle(fontSize: 13, color: isDark ? Colors.white70 : Colors.black87, height: 1.4),
                              ),
                            
                            if (isImage || isMaliciousDocument || (analysis.explanation?.mediaScanDetails.isNotEmpty ?? false)) ...[
                              const SizedBox(height: 8),
                              Container(
                                width: double.infinity,
                                padding: const EdgeInsets.all(10),
                                decoration: BoxDecoration(
                                  color: Colors.purple.withValues(alpha: 0.08),
                                  border: Border.all(color: Colors.purple.withValues(alpha: 0.3)),
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Row(
                                      children: [
                                        const Icon(Icons.troubleshoot, size: 14, color: Colors.purple),
                                        const SizedBox(width: 4),
                                        Text('Custom CvT-13 Analysis:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 11, color: Colors.purple.shade400)),
                                      ],
                                    ),
                                    const SizedBox(height: 6),
                                    if (analysis.explanation?.mediaScanDetails.isNotEmpty ?? false)
                                      Text(analysis.explanation!.mediaScanDetails, style: TextStyle(fontSize: 12, color: isDark ? Colors.white70 : Colors.black87, fontWeight: FontWeight.w500))
                                    else
                                      Text(analysis.reasons.join("\n"), style: TextStyle(fontSize: 12, color: isDark ? Colors.white70 : Colors.black87)),
                                    
                                    if (analysis.explanation?.manipulationSigns.isNotEmpty ?? false) ...[
                                      const SizedBox(height: 6),
                                      ...analysis.explanation!.manipulationSigns.map((sign) => Padding(
                                        padding: const EdgeInsets.only(top: 2),
                                        child: Row(
                                          crossAxisAlignment: CrossAxisAlignment.start,
                                          children: [
                                            Text('• ', style: TextStyle(color: Colors.purple.shade300, fontSize: 12)),
                                            Expanded(child: Text(sign, style: TextStyle(fontSize: 11, color: isDark ? Colors.white60 : Colors.black54))),
                                          ],
                                        ),
                                      )),
                                    ]
                                  ],
                                ),
                              ),
                            ],
                            const SizedBox(height: 12),
                            
                            if (!isImage && analysis.explanation!.realVsFakeData.isNotEmpty) ...[
                              Container(
                                width: double.infinity,
                                padding: const EdgeInsets.all(10),
                                decoration: BoxDecoration(
                                  color: isFake ? (isDark ? Colors.red.withValues(alpha: 0.12) : Colors.red.shade50) : (isDark ? Colors.blueGrey.withValues(alpha: 0.2) : Colors.blue.shade50),
                                  borderRadius: BorderRadius.circular(10),
                                  border: Border.all(color: isFake ? Colors.red.withValues(alpha: 0.3) : Colors.blue.withValues(alpha: 0.3)),
                                ),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Row(
                                      children: [
                                        Icon(isFake ? Icons.gpp_maybe_rounded : Icons.lightbulb_outline, size: 16, color: isFake ? Colors.red : Colors.blue),
                                        const SizedBox(width: 8),
                                        Text(isFake ? 'AI REALITY CHECK' : 'AI SUGGESTION', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: isFake ? Colors.red.shade900 : Colors.blue.shade900)),
                                      ],
                                    ),
                                    const SizedBox(height: 8),
                                    Text(analysis.explanation!.realVsFakeData, style: TextStyle(fontSize: 12, color: isFake ? (isDark ? Colors.red.shade200 : Colors.red.shade900) : (isDark ? Colors.blue.shade200 : Colors.blue.shade900), height: 1.3)),
                                  ],
                                ),
                              ),
                              const SizedBox(height: 12),
                            ],

                            if (!isImage && analysis.explanation!.entities.isNotEmpty) ...[
                               Text('ENTITY CONTEXT', style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: isDark ? Colors.white54 : Colors.black45)),
                               const SizedBox(height: 6),
                               SingleChildScrollView(
                                 scrollDirection: Axis.horizontal,
                                 child: Row(
                                   children: analysis.explanation!.entities.map((entity) => Container(
                                     margin: const EdgeInsets.only(right: 8),
                                     padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                     decoration: BoxDecoration(color: isDark ? Colors.white12 : Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: Colors.black12)),
                                     child: Column(
                                       crossAxisAlignment: CrossAxisAlignment.start,
                                       children: [
                                         Text(entity.name, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
                                         if (entity.role.isNotEmpty) Text(entity.role, style: const TextStyle(fontSize: 9, color: Colors.grey)),
                                       ],
                                     ),
                                   )).toList(),
                                 ),
                               ),
                               const SizedBox(height: 12),
                            ],

                            if (!isImage && analysis.explanation!.claimVsReality.isNotEmpty) ...[
                               Text('CLAIM VS REALITY', style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: isDark ? Colors.white54 : Colors.black45)),
                               const SizedBox(height: 6),
                               ...analysis.explanation!.claimVsReality.map((item) => Container(
                                 margin: const EdgeInsets.only(bottom: 8),
                                 padding: const EdgeInsets.all(8),
                                 decoration: BoxDecoration(color: isDark ? Colors.red.withValues(alpha: 0.05) : Colors.red.shade50.withValues(alpha: 0.3), borderRadius: BorderRadius.circular(8), border: Border.all(color: Colors.red.withValues(alpha: 0.1))),
                                 child: Column(
                                   crossAxisAlignment: CrossAxisAlignment.start,
                                   children: [
                                     Row(crossAxisAlignment: CrossAxisAlignment.start, children: [const Text('❌ Claim: ', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Colors.red)), Expanded(child: Text(item.claim, style: const TextStyle(fontSize: 11)))]),
                                     const SizedBox(height: 4),
                                     Row(crossAxisAlignment: CrossAxisAlignment.start, children: [const Text('✅ Reality: ', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Colors.green)), Expanded(child: Text(item.reality, style: const TextStyle(fontSize: 11)))]),
                                   ],
                                 ),
                               )),
                               const SizedBox(height: 12),
                            ],

                            if (!isImage && analysis.explanation!.whyFake.isNotEmpty) ...[
                               Text('WHY IT IS RISKY', style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: isDark ? Colors.white54 : Colors.black45)),
                               const SizedBox(height: 4),
                               ...analysis.explanation!.whyFake.map((r) => Padding(padding: const EdgeInsets.only(top: 4), child: Text('- $r', style: TextStyle(fontSize: 11, color: isFake ? Colors.red.shade900 : Colors.grey.shade700)))),
                            ],
                            
                            if (isFake && !isImage) ...[
                              const SizedBox(height: 12),
                              SizedBox(
                                width: double.infinity,
                                child: OutlinedButton.icon(
                                  onPressed: () => context.read<ChatProvider>().deleteMessage(widget.message.chatId, widget.message.id),
                                  style: OutlinedButton.styleFrom(side: const BorderSide(color: Colors.red), foregroundColor: Colors.red, padding: const EdgeInsets.symmetric(vertical: 2), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8))),
                                  icon: const Icon(Icons.delete_forever, size: 16),
                                  label: const Text('Delete for Everyone', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                                ),
                              ),
                            ],
                          ] else if (!isImage && analysis.reasons.isNotEmpty) ...[
                            ...analysis.reasons.map((r) => Padding(padding: const EdgeInsets.only(top: 4), child: Text('- $r', style: const TextStyle(fontSize: 12, color: Colors.grey)))),
                          ],
                        ],
                      ),
                    ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildContentWithHighlight(String text, String? query, Color textColor) {
    return Linkify(
      onOpen: (link) async {
        final uri = Uri.parse(link.url);
        try { if (await canLaunchUrl(uri)) await launchUrl(uri, mode: LaunchMode.externalApplication); } catch (e) { debugPrint('Error launching URL: $e'); }
      },
      text: text,
      style: TextStyle(fontSize: 16, color: textColor),
      linkStyle: const TextStyle(color: Colors.blue, decoration: TextDecoration.underline, fontWeight: FontWeight.w600),
    );
  }

  Widget _buildImageContent(BuildContext context, Message message, bool isDark) {
    final isNSFW = message.analysisResult?.explanation?.isNSFW ?? false;
    final showImage = !isNSFW || _isNSFWUnveiled;
    return ClipRRect(
      borderRadius: BorderRadius.circular(8),
      child: Stack(
        alignment: Alignment.center,
        children: [
          ImageFiltered(
            imageFilter: ImageFilter.blur(sigmaX: (!showImage) ? 30 : 0, sigmaY: (!showImage) ? 30 : 0),
            child: message.content.startsWith('http')
                ? Image.network(message.content, width: double.infinity, fit: BoxFit.cover, loadingBuilder: (context, child, lp) => lp == null ? child : Container(height: 200, color: isDark ? Colors.grey[900] : Colors.grey[200], child: const Center(child: CircularProgressIndicator(strokeWidth: 2))), errorBuilder: (context, error, st) => Container(height: 100, color: Colors.red.withValues(alpha: 0.1), child: const Center(child: Icon(Icons.broken_image, color: Colors.red))))
                : Image.file(File(message.content), width: double.infinity, fit: BoxFit.cover, errorBuilder: (context, error, st) => Container(height: 100, color: Colors.grey.withValues(alpha: 0.1), child: const Center(child: Icon(Icons.image_not_supported)))),
          ),
          if (!showImage) BackdropFilter(filter: ImageFilter.blur(sigmaX: 5, sigmaY: 5), child: Container(padding: const EdgeInsets.all(16), decoration: BoxDecoration(color: Colors.black.withValues(alpha: 0.6)), child: Column(mainAxisSize: MainAxisSize.min, children: [const Icon(Icons.visibility_off, color: Colors.white, size: 36), const SizedBox(height: 12), const Text("Sensitive Content", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16)), const SizedBox(height: 6), Text("This image has been flagged for potentially sensitive or adult content.", style: TextStyle(color: Colors.white.withValues(alpha: 0.8), fontSize: 12), textAlign: TextAlign.center), const SizedBox(height: 20), ElevatedButton(onPressed: () => setState(() => _isNSFWUnveiled = true), style: ElevatedButton.styleFrom(backgroundColor: Colors.redAccent, foregroundColor: Colors.white, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)), padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12)), child: const Text("SHOW CONTENT", style: TextStyle(fontWeight: FontWeight.bold)))]))),
        ],
      ),
    );
  }
}
