import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:permission_handler/permission_handler.dart';

class QrScannerScreen extends StatefulWidget {
  const QrScannerScreen({super.key});

  @override
  State<QrScannerScreen> createState() => _QrScannerScreenState();
}

class _QrScannerScreenState extends State<QrScannerScreen> {
  final MobileScannerController controller = MobileScannerController(
    detectionSpeed: DetectionSpeed.normal,
    facing: CameraFacing.back,
    torchEnabled: false,
  );

  bool _hasPermission = false;
  bool _isCheckingPermission = true;

  Future<void> _checkPermission() async {
    final status = await Permission.camera.status;
    if (status.isGranted) {
      if (mounted) {
        setState(() {
          _hasPermission = true;
          _isCheckingPermission = false;
        });
      }
    } else {
      final result = await Permission.camera.request();
      if (mounted) {
        setState(() {
          _hasPermission = result.isGranted;
          _isCheckingPermission = false;
        });
      }
    }
  }

  @override
  void initState() {
    super.initState();
    _checkPermission();
  }

  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Scan QR Code'),
        backgroundColor: const Color(0xFF075E54),
      ),
      body: _isCheckingPermission
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF00A884)))
          : !_hasPermission
              ? _buildPermissionDeniedView()
              : _buildScannerView(),
    );
  }

  Widget _buildPermissionDeniedView() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.camera_alt_outlined, size: 60, color: Colors.grey),
            const SizedBox(height: 20),
            const Text(
              'Camera permission is required to scan QR codes.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 16),
            ),
            const SizedBox(height: 30),
            ElevatedButton(
              onPressed: _checkPermission,
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF00A884),
              ),
              child: const Text('Grant Permission'),
            ),
            TextButton(
              onPressed: () => openAppSettings(),
              child: const Text('Open Settings', style: TextStyle(color: Color(0xFF00A884))),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildScannerView() {
    return Stack(
      children: [
        MobileScanner(
          controller: controller,
          onDetect: (capture) {
            final List<Barcode> barcodes = capture.barcodes;
            for (final barcode in barcodes) {
              final String? code = barcode.rawValue;
              if (code != null && code.startsWith('SAFETY_')) {
                controller.stop();
                Navigator.pop(context, code);
                break;
              }
            }
          },
        ),
        // Custom Viewfinder Overlay
        Center(
          child: Container(
            width: 250,
            height: 250,
            decoration: BoxDecoration(
              border: Border.all(color: const Color(0xFF00A884), width: 4),
              borderRadius: BorderRadius.circular(12),
            ),
          ),
        ),
        const Positioned(
          bottom: 50,
          left: 0,
          right: 0,
          child: Center(
            child: Text(
              'Align the MisLEADING ID QR within the box',
              style: TextStyle(
                color: Colors.white,
                backgroundColor: Colors.black54,
                fontSize: 14,
              ),
            ),
          ),
        ),
      ],
    );
  }
}
