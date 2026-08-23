import shutil
from pathlib import Path

"""
Generic utility functions for file and directory management.
"""

def clear_directory(folder: str | Path):
    """
    Clears all files and subdirectories in the specified folder.

    Args:
        folder (Path): Path to the folder to clear.
    """
    folder = Path(folder)
    for file_path in folder.iterdir():
        if file_path.name == ".gitkeep":
            continue
        try:
            if file_path.is_file() or file_path.is_symlink():
                file_path.unlink()
            elif file_path.is_dir():
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

def ask_which_file(dir_path: str | Path, file_ext: str, message: str) -> str:
    """
    Asks user to select file in given directory

    Args:
        dir_path (str): Path to the directory containing files.
        file_ext (str): File extension to filter files by.
        message (str): Message to display to the user when asking for input.
    Returns:
        str: The name of the selected file.
    """
    # List all available files in directory
    file_list = [file_path.name for file_path in Path(dir_path).iterdir()
                 if file_ext in file_path.name]
    if not file_list:
        raise FileNotFoundError(f"No files with extension '{file_ext}' found in directory '{dir_path}'.")
    for a, e in enumerate(file_list):
        print(str(a) + '. ' + e)

    # Ask user which one to return
    inp = input(f"{message}\n")
    while not (0 <= (number := int(inp)) <= (len(file_list) - 1)):
        inp = input("Please enter the number next to a file):\n")
    selected_file = file_list[int(inp)]

    return selected_file