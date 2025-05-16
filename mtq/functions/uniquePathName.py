import os

def uniquePathName(file_path:str):
    """
    Returns a unique file or directory path by appending an underscore and a number if the path already exists.

    Args:
    - path (str): The initial file or directory path.

    Returns: A unique file or directory path.
    """
    if not os.path.exists(file_path):
        return file_path

    base, ext = os.path.splitext(file_path)
    counter = 1

    while True:
        new_path = f"{base}_{counter}{ext}"
        if not os.path.exists(new_path):
            return new_path
        counter += 1