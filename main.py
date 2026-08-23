import src.nac
import src.utils

"""
Run this script to process NAC images a search area of your choice.
"""

## Comment out this line if you want to keep your logs from previous runs.
## Note that reprocessing the same area will overwrite the previous log, so if
## you want to keep them, move them to a different folder first.
#src.utils.clear_directory("logs")

# Main function to process NAC images in a search area.
src.nac.process_search_area()