import os
import subprocess
import sys

"""
Produces 60 meter scale dem of lunar globe in +-60degrees from the SLDEM2015
product at https://pgda.gsfc.nasa.gov/products/54

1. Download all 512 pixels / degree float img format .lbl and .img files from
https://imbrium.mit.edu/DATA/SLDEM2015/TILES/FLOAT_IMG/ It can be helpful to use
a browser plugin to download all at once and delete the files that start with
256

2. Make sure to increase the maximum allowable file size in ISIS preferences to
44 or so to account for the final product's size (approximately 43 gb):
"The maximum value can be changed in your personal preference file located in
[~/.Isis/IsisPreferences] within the group CubeCustomization,
keyword MaximumSize. If you do not have an ISISPreference file, please refer to
the documentation 'Environment and Preference Setup'."

3. Change the SLDEM_FILES variable to the directory path you saved the sldem
files in.

4. Run this script. The final product "SLDEM.demprep.cub" will be in the same 
directory.

NOTE: This script doesn't automatically delete files, the final folder size will
be approximately 226.5 gb total, please make sure your drive has enough room or
modify this script to delete files as they are processed.
"""

SLDEM_FILES = '/home/user/Downloads/sldem_files'

def get_lbl_img_pairs(dir_name: str) -> tuple:
    # Get lbl and img file pairs
    file_list = [f for f in os.listdir(dir_name) if '.LBL' in f or '.IMG' in f]
    pairs = {}
    missing = []
    for f in file_list:
        fname, fext = os.path.splitext(f)
        lbl = file_list[file_list.index(fname + '.LBL')]
        img = file_list[file_list.index(fname + '.IMG')]
        cub = fname.replace('_FLOAT', '') + '.cub'
        if lbl is not None and img is not None:
            pairs[fname] = [lbl, img, cub]
        else:
            missing.append(f)

    ## Manual check
    #print(len(pairs))
    #for item in pairs:
    #    print(item)
    #print("Following files are missing it's pair")
    #print(missing)
#
    return pairs, missing

def sldem_to_cub(lbl_file, cub_file):
    if os.path.exists(os.path.join(SLDEM_FILES, cub_file)):
        print(f'{cub_file} already created')
        return
    bash_command = [
        'bash',
        'sldem_preprocess/sldem_to_cub.sh',
        lbl_file,
        cub_file,
        SLDEM_FILES
    ]
    # Start the process with a pipe for standard output
    with subprocess.Popen(bash_command, stdout=subprocess.PIPE, text=True) as process:
        # Read and print line-by-line as it streams
        for line in process.stdout:
            print(line, end='')  # end='' prevents double line break

def preprocess_sldems():
    sldems, missing = get_lbl_img_pairs(SLDEM_FILES)
    for item in sldems:
        sldem_to_cub(sldems[item][0], sldems[item][2])
    if missing != []:
        print("Following files are missing either the .lbl or .img file")
        print(missing)
        sys.exit()

def write_list_of_cubs():
    with open(os.path.join(SLDEM_FILES, 'sldem.lis'), 'w') as f:
        f.writelines([x + '\n' for x in os.listdir(SLDEM_FILES) if x.endswith('.cub')])

def mosaic_sldems():
    bash_command = [
        'bash',
        'sldem_preprocess/mosaic_sldem.sh',
        SLDEM_FILES
    ]
    # Start the process with a pipe for standard output
    with subprocess.Popen(bash_command, stdout=subprocess.PIPE, text=True) as process:
        # Read and print line-by-line as it streams
        for line in process.stdout:
            print(line, end='')  # end='' prevents double line break

preprocess_sldems()
write_list_of_cubs()
mosaic_sldems()