def safe_iter(obj, attr: str):
    """Helper function to safely iterate over object attributes"""
    return getattr(obj, attr, []) or []


def get_file_extension(content_type: str) -> str:
    """Infer file extension from content type"""
    if "jpeg" in content_type:
        return ".jpg"
    elif "png" in content_type:
        return ".png"
    elif "video" in content_type or "mp4" in content_type:
        return ".mp4"
    return ".bin"
