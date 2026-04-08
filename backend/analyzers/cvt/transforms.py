from torchvision import transforms

def get_transform():
    """
    Standard CvT-13 transforms used during training:
    - Resize to 200x200
    - ToTensor
    - ImageNet normalization
    """
    return transforms.Compose([
        transforms.Resize((200, 200)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
