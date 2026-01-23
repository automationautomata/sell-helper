import base64
import os
import uuid


def image_to_base64(img_path: str) -> str:
    with open(img_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def generate_file_name(filepath: str) -> str:
    path = os.path.dirname(filepath)
    _, ext = os.path.splitext(filepath)
    name = uuid.uuid4().hex
    return os.path.join(path, f"{name}{ext}")
