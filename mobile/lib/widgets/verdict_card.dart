import 'package:flutter/material.dart';
import '../models/message.dart';

class VerdictCard extends StatefulWidget {
  final ScanResult result;

  const VerdictCard({super.key, required this.result});

  @override
  State<VerdictCard> createState() => _VerdictCardState();
}

class _VerdictCardState extends State<VerdictCard> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    Color verdictColor;
    IconData verdictIcon;

    switch (widget.result.verdict.toUpperCase()) {
      case 'FAKE':
        verdictColor = Colors.redAccent;
        verdictIcon = Icons.dangerous;
        break;
      case 'MISLEADING':
        verdictColor = Colors.orangeAccent;
        verdictIcon = Icons.warning;
        break;
      case 'SAFE':
      default:
        verdictColor = Colors.green;
        verdictIcon = Icons.check_circle;
    }

    return GestureDetector(
      onTap: () {
        setState(() {
          _expanded = !_expanded;
        });
      },
      child: Container(
        margin: const EdgeInsets.only(top: 8),
        decoration: BoxDecoration(
          color: verdictColor.withValues(alpha: 0.1),
          border: Border.all(color: verdictColor.withValues(alpha: 0.5), width: 1),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Header
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
              decoration: BoxDecoration(
                color: verdictColor.withValues(alpha: 0.2),
                borderRadius: const BorderRadius.vertical(top: Radius.circular(8)),
              ),
              child: Row(
                children: [
                  Icon(verdictIcon, size: 16, color: verdictColor),
                  const SizedBox(width: 6),
                  Text(
                    widget.result.verdict.toUpperCase(),
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 12,
                      color: verdictColor,
                    ),
                  ),
                  const Spacer(),
                  Text(
                    'Risk: ${widget.result.riskScore}%',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 12,
                      color: verdictColor,
                    ),
                  ),
                ],
              ),
            ),
            
            // Expandable Content
            if (_expanded && widget.result.reasons.isNotEmpty)
              Padding(
                padding: const EdgeInsets.all(8.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'AI Analysis Reasons:',
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                        color: Colors.white70,
                      ),
                    ),
                    const SizedBox(height: 4),
                    ...widget.result.reasons.map((reason) => Padding(
                          padding: const EdgeInsets.only(bottom: 4.0),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text('• ', style: TextStyle(color: Colors.white70)),
                              Expanded(
                                child: Text(
                                  reason,
                                  style: const TextStyle(fontSize: 12, color: Colors.white70),
                                ),
                              ),
                            ],
                          ),
                        )),
                  ],
                ),
              ),
              
            if (!_expanded && widget.result.reasons.isNotEmpty)
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 4),
                child: Center(
                  child: Icon(Icons.keyboard_arrow_down, size: 16, color: Colors.white54),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
