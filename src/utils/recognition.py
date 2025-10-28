import cv2
from pyzbar import pyzbar


def extract_barcodes(img_path: str) -> list[str]:
    """
    Extract barcodes from an image file.

    Args:
        img_path (str): Path to the image file containing barcodes

    Returns:
        list[str]: List of decoded barcode values as strings
    """
    image = cv2.imread(img_path)

    barcodes = pyzbar.decode(image)
    return [barcode.data.decode("utf-8") for barcode in barcodes]
