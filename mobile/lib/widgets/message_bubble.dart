import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/message.dart';
import 'verdict_card.dart';
import 'explosion_widget.dart';

class MessageBubble extends StatelessWidget {
  final Message message;

  const MessageBubble({super.key, required this.message});

  @override
  Widget build(BuildContext context) {
    bool isDark = Theme.of(context).brightness == Brightness.dark;
    
    // Bubble colors typical of WA
    Color bubbleColor = message.isMe 
        ? (isDark ? const Color(0xFF005C4B) : const Color(0xFFD9FDD3))
        : (isDark ? const Color(0xFF202C33) : Colors.white);
        
    Color textColor = isDark ? Colors.white : Colors.black87;
    
    // If deleted, we replace the entire block with the placeholder
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
              Icon(Icons.block, size: 14, color: isDark ? Colors.white54 : Colors.black54),
              const SizedBox(width: 6),
              Text(
                "This message was deleted due to Fake News",
                style: TextStyle(
                  fontSize: 14,
                  fontStyle: FontStyle.italic,
                  color: isDark ? Colors.white54 : Colors.black54
                ),
              ),
            ],
          ),
        ),
      );
    }

    return ExplosionWidget(
      isDeleted: message.analysisResult?.verdict == 'FAKE' && message.isDeleted == false,
      child: Column(
        crossAxisAlignment: message.isMe ? CrossAxisAlignment.end : CrossAxisAlignment.start,
        children: [
          Align(
            alignment: message.isMe ? Alignment.centerRight : Alignment.centerLeft,
            child: Container(
              margin: const EdgeInsets.symmetric(vertical: 2.0),
              decoration: BoxDecoration(
                color: bubbleColor,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Stack(
                children: [
                  Padding(
                    padding: const EdgeInsets.only(
                      left: 10, 
                      right: 48, // space for time + ticks + spinner
                      top: 8, 
                      bottom: 12
                    ),
                    child: Text(
                      message.content,
                      style: TextStyle(fontSize: 16, color: textColor),
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
                          style: TextStyle(
                            fontSize: 11,
                            color: isDark ? Colors.white60 : Colors.black54,
                          ),
                        ),
                        if (message.isMe) ...[
                          const SizedBox(width: 4),
                          // The Loading Spinner inline!
                          if (message.isAnalyzing)
                            const SizedBox(
                              width: 12,
                              height: 12,
                              child: CircularProgressIndicator(strokeWidth: 2, color: Colors.blueAccent),
                            )
                          else
                            const Icon(Icons.done_all, size: 16, color: Colors.blue), // Blue ticks
                        ]
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
          
          // Verdict Card - Only show if it's NOT safe (SAFE gets hidden entirely)
          if (!message.isAnalyzing && 
              message.analysisResult != null && 
              message.analysisResult!.verdict != 'SAFE' && 
              message.analysisResult!.verdict != 'UNKNOWN')
            VerdictCard(result: message.analysisResult!),
        ],
      ),
    );
  }
}
