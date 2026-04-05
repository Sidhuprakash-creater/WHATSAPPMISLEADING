import 'dart:math';
import 'package:flutter/material.dart';

class ExplosionWidget extends StatefulWidget {
  final Widget child;
  final bool isDeleted;

  const ExplosionWidget({super.key, required this.child, required this.isDeleted});

  @override
  State<ExplosionWidget> createState() => _ExplosionWidgetState();
}

class _ExplosionWidgetState extends State<ExplosionWidget> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  bool _exploded = false;
  final int particleCount = 40;
  List<Particle> particles = [];

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(vsync: this, duration: const Duration(milliseconds: 600));
    _controller.addListener(() {
      setState(() {});
    });
  }

  @override
  void didUpdateWidget(ExplosionWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.isDeleted && !oldWidget.isDeleted) {
      _triggerExplosion();
    }
  }

  void _triggerExplosion() {
    final random = Random();
    particles = List.generate(particleCount, (index) {
      return Particle(
        x: 0,
        y: 0,
        direction: random.nextDouble() * 2 * pi,
        speed: random.nextDouble() * 100 + 50,
        color: const Color(0xFF005C4B), // Custom WhatsApp green for particles
        size: random.nextDouble() * 6 + 2,
      );
    });
    setState(() {
      _exploded = true;
    });
    _controller.forward();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (!widget.isDeleted && !_exploded) {
      return widget.child;
    }

    if (_controller.isCompleted) {
      return const SizedBox.shrink(); // Completely gone
    }

    return LayoutBuilder(
      builder: (context, constraints) {
        return CustomPaint(
          size: Size(constraints.maxWidth, constraints.maxHeight),
          painter: ParticlePainter(particles, _controller.value),
          child: Opacity(
            opacity: 1.0 - _controller.value,
            child: widget.child,
          ),
        );
      },
    );
  }
}

class Particle {
  final double x;
  final double y;
  final double direction;
  final double speed;
  final Color color;
  final double size;

  Particle({required this.x, required this.y, required this.direction, required this.speed, required this.color, required this.size});
}

class ParticlePainter extends CustomPainter {
  final List<Particle> particles;
  final double progress;

  ParticlePainter(this.particles, this.progress);

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint();
    final center = Offset(size.width / 2, size.height / 2);

    for (var particle in particles) {
      final currentSpeed = particle.speed * progress;
      final dx = center.dx + cos(particle.direction) * currentSpeed;
      final dy = center.dy + sin(particle.direction) * currentSpeed;

      paint.color = particle.color.withValues(alpha: 1.0 - progress);
      canvas.drawCircle(Offset(dx, dy), particle.size * (1 - progress), paint);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}
