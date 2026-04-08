import os
import glob
import torch
import logging
from PIL import Image
from .cvt.model import get_model
from .cvt.transforms import get_transform

logger = logging.getLogger(__name__)

class CVTDetector:
    def __init__(self, weights_dir=None):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.transform = get_transform()
        self.weights_dir = weights_dir or os.path.join(os.path.dirname(__file__), "..", "models", "cvt")
        self.is_loaded = False
        
        # Initialize architecture but don't load weights yet
        try:
            self.model = get_model(self.device).eval()
        except Exception as e:
            logger.error(f"Failed to initialize CvT Architecture: {e}")

    def load_latest_weights(self):
        """Loads the latest .pth file from the weights directory."""
        if not self.model:
            return False
            
        try:
            list_of_files = glob.glob(os.path.join(self.weights_dir, 'model_epoch_*.pth'))
            if not list_of_files:
                logger.warning(f"No custom CvT weights found in {self.weights_dir}. Using base model.")
                return False
                
            latest_file = max(list_of_files, key=os.path.getctime)
            logger.info(f"Loading custom CvT weights from: {latest_file}")
            
            checkpoint = torch.load(latest_file, map_location=self.device)
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.is_loaded = True
            return True
        except Exception as e:
            logger.error(f"Failed to load CvT weights: {e}")
            return False

    async def predict(self, pil_image: Image.Image):
        """Runs a prediction on the provided PIL image."""
        if not self.model:
            return None
            
        try:
            # Ensure proper mode
            if pil_image.mode != "RGB":
                pil_image = pil_image.convert("RGB")
                
            transformed_image = self.transform(pil_image).unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                outputs = self.model(transformed_image)
                # Map numeric labels to string labels
                label_map = {0: "real", 1: "fake"}
                
                # If architecture has logits (from transformers backbone)
                if hasattr(outputs, 'logits'):
                    logits = outputs.logits
                else:
                    logits = outputs
                    
                _, predicted = logits.max(1)
                probabilities = torch.nn.functional.softmax(logits, dim=1)
                
                predicted_label = label_map[predicted.item()]
                confidence = probabilities[0][predicted.item()].item() * 100
                
                return {
                    "label": predicted_label,
                    "confidence": confidence,
                    "probabilities": probabilities.tolist()
                }
        except Exception as e:
            logger.error(f"CvT Prediction Error: {e}")
            return None

# Singleton instance for lazy loading
_scanner = None

def get_cvt_scanner():
    global _scanner
    if _scanner is None:
        _scanner = CVTDetector()
        _scanner.load_latest_weights()
    return _scanner
