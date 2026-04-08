import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../models/message.dart';

class VerdictCard extends StatefulWidget {
  final ScanResult result;
  const VerdictCard({super.key, required this.result});

  @override
  State<VerdictCard> createState() => _VerdictCardState();
}

class _VerdictCardState extends State<VerdictCard>
    with SingleTickerProviderStateMixin {
  bool _expanded = false;
  late AnimationController _animController;
  late Animation<double> _expandAnim;

  @override
  void initState() {
    super.initState();
    _animController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 300),
    );
    _expandAnim = CurvedAnimation(
      parent: _animController,
      curve: Curves.easeInOut,
    );
  }

  @override
  void dispose() {
    _animController.dispose();
    super.dispose();
  }

  void _toggle() {
    setState(() => _expanded = !_expanded);
    _expanded ? _animController.forward() : _animController.reverse();
  }

  // ── Verdict colours ───────────────────────────────────────
  Color get _verdictColor {
    final v = widget.result.verdict.toUpperCase();
    if (v.contains('HIGH')) return const Color(0xFFEF4444);
    if (v.contains('MEDIUM')) return const Color(0xFFF97316);
    return const Color(0xFF22C55E);
  }

  IconData get _verdictIcon {
    final v = widget.result.verdict.toUpperCase();
    if (v.contains('HIGH')) return Icons.dangerous_rounded;
    if (v.contains('MEDIUM')) return Icons.warning_amber_rounded;
    return Icons.verified_rounded;
  }

  String get _verdictLabel {
    final v = widget.result.verdict.toUpperCase();
    if (v.contains('HIGH') || v == 'FAKE') return '🔴 HIGH RISK — FAKE';
    if (v.contains('MEDIUM') || v == 'MISLEADING') return '🟠 MEDIUM RISK — MISLEADING';
    return '🟢 SAFE';
  }

  @override
  Widget build(BuildContext context) {
    final color = _verdictColor;
    final exp = widget.result.explanation;
    final hasRich = exp != null && !exp.isEmpty;

    return GestureDetector(
      onTap: _toggle,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 250),
        margin: const EdgeInsets.only(top: 8),
        decoration: BoxDecoration(
          color: const Color(0xFF1A1A2E),
          border: Border.all(color: color.withValues(alpha: 0.6), width: 1.5),
          borderRadius: BorderRadius.circular(12),
          boxShadow: [
            BoxShadow(
              color: color.withValues(alpha: 0.15),
              blurRadius: 12,
              spreadRadius: 1,
            )
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // ── Header Bar ─────────────────────────────────
            _Header(
              label: _verdictLabel,
              icon: _verdictIcon,
              color: color,
              score: widget.result.riskScore,
              expanded: _expanded,
            ),

            // ── Expandable Body ────────────────────────────
            SizeTransition(
              sizeFactor: _expandAnim,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const Divider(color: Colors.white12, height: 1),

                  // Primary Claim Box
                  if (hasRich && exp.primaryClaim.isNotEmpty)
                    _ClaimBox(claim: exp.primaryClaim),

                  // Why Fake
                  if (hasRich && exp.whyFake.isNotEmpty)
                    _Section(
                      icon: '❌',
                      title: 'WHY THIS IS RISKY',
                      child: _BulletList(items: exp.whyFake, color: color),
                    ),

                  // Claim vs Reality
                  if (hasRich && exp.claimVsReality.isNotEmpty)
                    _Section(
                      icon: '⚖️',
                      title: 'CLAIM vs REALITY',
                      child: Column(
                        children: exp.claimVsReality
                            .map((c) => _ClaimRealityRow(cvr: c)).toList(),
                      ),
                    ),

                  // People / Entities Mentioned
                  if (hasRich && exp.entities.isNotEmpty)
                    _Section(
                      icon: '👤',
                      title: 'PEOPLE / ORGANISATIONS MENTIONED',
                      child: Column(
                        children: exp.entities
                            .map((e) => _EntityCard(entity: e)).toList(),
                      ),
                    ),

                  // Real-time Web Evidence
                  if (hasRich && exp.realVsFakeData.isNotEmpty)
                    _Section(
                      icon: '🌐',
                      title: 'REAL-TIME FACT CHECK',
                      child: Container(
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: const Color(0xFF0F3460).withValues(alpha: 0.5),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(
                          exp.realVsFakeData,
                          style: const TextStyle(
                            fontSize: 12,
                            color: Colors.white70,
                            height: 1.5,
                          ),
                        ),
                      ),
                    ),

                  // Manipulation Patterns
                  if (hasRich && exp.patternsFound.isNotEmpty)
                    _Section(
                      icon: '🎭',
                      title: 'MANIPULATION TACTICS DETECTED',
                      child: Wrap(
                        spacing: 6,
                        runSpacing: 6,
                        children: exp.patternsFound
                            .map((p) => _PatternChip(pattern: p)).toList(),
                      ),
                    ),

                  // Verified Sources
                  if (hasRich && exp.verifiedSources.isNotEmpty)
                    _Section(
                      icon: '🔗',
                      title: 'VERIFIED SOURCES',
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: exp.verifiedSources
                            .map((s) => _SourceLink(source: s)).toList(),
                      ),
                    ),

                  // Fallback: legacy reasons (if no rich data)
                  if (!hasRich && widget.result.reasons.isNotEmpty)
                    _Section(
                      icon: '🤖',
                      title: 'AI ANALYSIS',
                      child: _BulletList(
                          items: widget.result.reasons, color: color),
                    ),

                  // Safe-to-forward badge
                  if (hasRich)
                    _SafeToForwardBadge(safe: exp.safeToForward),

                  const SizedBox(height: 8),
                ],
              ),
            ),

            // Collapse hint when not expanded
            if (!_expanded)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Center(
                  child: Icon(Icons.keyboard_arrow_down_rounded,
                      size: 18, color: color.withValues(alpha: 0.7)),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// SUB-WIDGETS
// ─────────────────────────────────────────────────────────────────────────────

class _Header extends StatelessWidget {
  final String label;
  final IconData icon;
  final Color color;
  final int score;
  final bool expanded;

  const _Header({
    required this.label,
    required this.icon,
    required this.color,
    required this.score,
    required this.expanded,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.18),
        borderRadius: BorderRadius.vertical(
          top: const Radius.circular(11),
          bottom: expanded ? Radius.zero : const Radius.circular(11),
        ),
      ),
      child: Row(
        children: [
          Icon(icon, size: 17, color: color),
          const SizedBox(width: 6),
          Expanded(
            child: Text(
              label,
              style: TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 12,
                color: color,
                letterSpacing: 0.5,
              ),
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.25),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: color.withValues(alpha: 0.5)),
            ),
            child: Text(
              'Score $score/100',
              style: TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
          ),
          const SizedBox(width: 6),
          Icon(
            expanded
                ? Icons.keyboard_arrow_up_rounded
                : Icons.keyboard_arrow_down_rounded,
            size: 16,
            color: Colors.white38,
          ),
        ],
      ),
    );
  }
}

class _ClaimBox extends StatelessWidget {
  final String claim;
  const _ClaimBox({required this.claim});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.fromLTRB(10, 10, 10, 0),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: const Color(0xFF16213E),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.white12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            '📌  WHAT IS BEING CLAIMED',
            style: TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.bold,
              color: Colors.white38,
              letterSpacing: 0.8,
            ),
          ),
          const SizedBox(height: 5),
          Text(
            claim,
            style: const TextStyle(
              fontSize: 13,
              color: Colors.white,
              fontStyle: FontStyle.italic,
              height: 1.4,
            ),
          ),
        ],
      ),
    );
  }
}

class _Section extends StatelessWidget {
  final String icon;
  final String title;
  final Widget child;
  const _Section({required this.icon, required this.title, required this.child});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(10, 10, 10, 0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(icon, style: const TextStyle(fontSize: 13)),
              const SizedBox(width: 5),
              Text(
                title,
                style: const TextStyle(
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                  color: Colors.white38,
                  letterSpacing: 0.8,
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          child,
        ],
      ),
    );
  }
}

class _BulletList extends StatelessWidget {
  final List<String> items;
  final Color color;
  const _BulletList({required this.items, required this.color});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: items
          .map((item) => Padding(
                padding: const EdgeInsets.only(bottom: 5),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      margin: const EdgeInsets.only(top: 5, right: 8),
                      width: 5,
                      height: 5,
                      decoration: BoxDecoration(
                          color: color, shape: BoxShape.circle),
                    ),
                    Expanded(
                      child: Text(
                        item,
                        style: const TextStyle(
                            fontSize: 12, color: Colors.white70, height: 1.4),
                      ),
                    ),
                  ],
                ),
              )).toList(),
    );
  }
}

class _ClaimRealityRow extends StatelessWidget {
  final ClaimVsReality cvr;
  const _ClaimRealityRow({required this.cvr});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.white10),
      ),
      child: Column(
        children: [
          // Claim row
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
            decoration: const BoxDecoration(
              color: Color(0x22EF4444),
              borderRadius: BorderRadius.vertical(top: Radius.circular(7)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('❌  CLAIM',
                    style: TextStyle(
                        fontSize: 9,
                        color: Color(0xFFEF4444),
                        fontWeight: FontWeight.bold,
                        letterSpacing: 0.7)),
                const SizedBox(height: 3),
                Text(cvr.claim,
                    style: const TextStyle(
                        fontSize: 12, color: Colors.white70, height: 1.3)),
              ],
            ),
          ),
          // Reality row
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
            decoration: const BoxDecoration(
              color: Color(0x2222C55E),
              borderRadius: BorderRadius.vertical(bottom: Radius.circular(7)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('✅  REALITY',
                    style: TextStyle(
                        fontSize: 9,
                        color: Color(0xFF22C55E),
                        fontWeight: FontWeight.bold,
                        letterSpacing: 0.7)),
                const SizedBox(height: 3),
                Text(cvr.reality,
                    style: const TextStyle(
                        fontSize: 12, color: Colors.white, height: 1.3)),
                if (cvr.sourceHint != null && cvr.sourceHint!.isNotEmpty) ...[
                  const SizedBox(height: 4),
                  Text('Verify: ${cvr.sourceHint}',
                      style: const TextStyle(
                          fontSize: 10,
                          color: Color(0xFF60A5FA),
                          fontStyle: FontStyle.italic)),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _EntityCard extends StatefulWidget {
  final RichEntity entity;
  const _EntityCard({required this.entity});

  @override
  State<_EntityCard> createState() => _EntityCardState();
}

class _EntityCardState extends State<_EntityCard> {
  bool _open = false;

  Color get _typeColor {
    switch (widget.entity.type) {
      case 'politician':
        return const Color(0xFFA78BFA);
      case 'businessman':
        return const Color(0xFFFBBF24);
      case 'celebrity':
        return const Color(0xFFF472B6);
      case 'institution':
        return const Color(0xFF60A5FA);
      default:
        return Colors.white38;
    }
  }

  IconData get _typeIcon {
    switch (widget.entity.type) {
      case 'politician':
        return Icons.account_balance_rounded;
      case 'businessman':
        return Icons.business_center_rounded;
      case 'celebrity':
        return Icons.star_rounded;
      case 'institution':
        return Icons.domain_rounded;
      default:
        return Icons.person_rounded;
    }
  }

  @override
  Widget build(BuildContext context) {
    final e = widget.entity;
    final tc = _typeColor;

    return GestureDetector(
      onTap: () => setState(() => _open = !_open),
      child: Container(
        margin: const EdgeInsets.only(bottom: 8),
        decoration: BoxDecoration(
          color: tc.withValues(alpha: 0.07),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: tc.withValues(alpha: 0.3)),
        ),
        child: Column(
          children: [
            // entity header
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(6),
                    decoration: BoxDecoration(
                      color: tc.withValues(alpha: 0.2),
                      shape: BoxShape.circle,
                    ),
                    child: Icon(_typeIcon, size: 14, color: tc),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(e.name,
                            style: TextStyle(
                                fontWeight: FontWeight.bold,
                                fontSize: 13,
                                color: tc)),
                        if (e.role.isNotEmpty)
                          Text(e.role,
                              style: const TextStyle(
                                  fontSize: 11, color: Colors.white54)),
                      ],
                    ),
                  ),
                  if (e.partyOrCompany != null)
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        color: tc.withValues(alpha: 0.2),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Text(
                        e.partyOrCompany!,
                        style: TextStyle(
                            fontSize: 9,
                            color: tc,
                            fontWeight: FontWeight.bold),
                      ),
                    ),
                  const SizedBox(width: 4),
                  Icon(_open ? Icons.expand_less : Icons.expand_more,
                      size: 16, color: Colors.white30),
                ],
              ),
            ),
            // expanded detail
            if (_open) ...[
              const Divider(color: Colors.white10, height: 1),
              Padding(
                padding: const EdgeInsets.fromLTRB(10, 8, 10, 10),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    if (e.detailedBackground != null &&
                        e.detailedBackground!.isNotEmpty) ...[
                      const Text('📝 DOSSIER:',
                          style: TextStyle(
                              fontSize: 9,
                              fontWeight: FontWeight.bold,
                              color: Colors.white38,
                              letterSpacing: 0.8)),
                      const SizedBox(height: 3),
                      Text(e.detailedBackground!,
                          style: const TextStyle(
                              fontSize: 12, color: Colors.white70, height: 1.4)),
                      const SizedBox(height: 8),
                    ],
                    if (e.wikipediaSummary != null &&
                        e.wikipediaSummary!.isNotEmpty) ...[
                      const Text('🌐 WIKIPEDIA SUMMARY:',
                          style: TextStyle(
                              fontSize: 9,
                              fontWeight: FontWeight.bold,
                              color: Colors.white38,
                              letterSpacing: 0.8)),
                      const SizedBox(height: 3),
                      Text(e.wikipediaSummary!,
                          style: const TextStyle(
                              fontSize: 11, color: Colors.white60, height: 1.4, fontStyle: FontStyle.italic)),
                      const SizedBox(height: 8),
                    ],
                    if (e.whyMentioned != null &&
                        e.whyMentioned!.isNotEmpty) ...[
                      _infoRow('Why mentioned:', e.whyMentioned!, Colors.white54),
                      const SizedBox(height: 4),
                    ],
                    if (e.misuseNote != null &&
                        e.misuseNote!.isNotEmpty)
                      Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: const Color(0x22EF4444),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text('⚠️ ',
                                style: TextStyle(fontSize: 11)),
                            Expanded(
                              child: Text(e.misuseNote!,
                                  style: const TextStyle(
                                      fontSize: 11,
                                      color: Color(0xFFFCA5A5),
                                      height: 1.3)),
                            ),
                          ],
                        ),
                      ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _infoRow(String label, String value, Color valueColor) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label,
            style: const TextStyle(fontSize: 10, color: Colors.white38)),
        const SizedBox(width: 4),
        Expanded(
            child: Text(value,
                style: TextStyle(fontSize: 11, color: valueColor))),
      ],
    );
  }
}

class _PatternChip extends StatelessWidget {
  final PatternFound pattern;
  const _PatternChip({required this.pattern});

  @override
  Widget build(BuildContext context) {
    return Tooltip(
      message: pattern.evidence,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        decoration: BoxDecoration(
          color: const Color(0xFF7C3AED).withValues(alpha: 0.2),
          borderRadius: BorderRadius.circular(12),
          border:
              Border.all(color: const Color(0xFF7C3AED).withValues(alpha: 0.5)),
        ),
        child: Text(
          pattern.type.replaceAll('_', ' '),
          style: const TextStyle(
            fontSize: 10,
            color: Color(0xFFC4B5FD),
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
    );
  }
}

class _SourceLink extends StatelessWidget {
  final VerifiedSource source;
  const _SourceLink({required this.source});

  Future<void> _launch(String url) async {
    final uri = Uri.tryParse(url);
    if (uri != null) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => _launch(source.url),
      child: Padding(
        padding: const EdgeInsets.only(bottom: 5),
        child: Row(
          children: [
            const Icon(Icons.open_in_new_rounded,
                size: 12, color: Color(0xFF60A5FA)),
            const SizedBox(width: 6),
            Expanded(
              child: Text(
                source.title,
                style: const TextStyle(
                  fontSize: 11,
                  color: Color(0xFF60A5FA),
                  decoration: TextDecoration.underline,
                  decorationColor: Color(0xFF60A5FA),
                ),
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _SafeToForwardBadge extends StatelessWidget {
  final bool safe;
  const _SafeToForwardBadge({required this.safe});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(10, 10, 10, 0),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(
          color: safe
              ? const Color(0x2222C55E)
              : const Color(0x22EF4444),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: safe
                ? const Color(0xFF22C55E).withValues(alpha: 0.4)
                : const Color(0xFFEF4444).withValues(alpha: 0.4),
          ),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(safe ? '✅' : '🚫', style: const TextStyle(fontSize: 14)),
            const SizedBox(width: 8),
            Text(
              safe
                  ? 'Safe to forward'
                  : 'DO NOT FORWARD — This may spread misinformation',
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.bold,
                color: safe
                    ? const Color(0xFF86EFAC)
                    : const Color(0xFFFCA5A5),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
