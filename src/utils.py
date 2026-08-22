import os
import shutil

"""
Generic utility functions for file and directory management.
"""

def clear_directory(folder: str):
    """
    Clears all files and subdirectories in the specified folder.

    Args:
        folder (Path): Path to the folder to clear.
    """
    for filename in os.listdir(folder):
        if filename == ".gitkeep":
            continue
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

def ask_which_file(dir_path: str, file_ext: str, message: str) -> str:
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
    file_list = [f for f in os.listdir(dir_path) if file_ext in f]
    for a, e in enumerate(file_list):
        print(str(a) + '. ' + e)

    # Ask user which one to return
    inp = input(f"{message}\n")
    while not (0 <= (number := int(inp)) <= (len(file_list) - 1)):
        inp = input("Please enter the number next to a file):\n")
    selected_file = file_list[int(inp)]

    return selected_file