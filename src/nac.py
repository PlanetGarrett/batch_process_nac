import json
import subprocess
import requests
from bs4 import BeautifulSoup
import urllib.request
import time
import shutil
import src.utils
from pathlib import Path
from tqdm import trange

"""
Functions for downloading and processing LRO NAC images listed in Quickmap geojson files.

If you want to use a user-provided DEM for processing, set USER_DEM to 'true'.
Set DEM_PATH to the path of the DEM to use for processing.

If you want to perform photometric correction, set PERFORM_PHOTOMET to 'true'. 
This option is generally not recommended due to processing times and relatively 
small benefits.

If you want to convert the output to .tif format, set CONVERT_TO_TIF to 'true'.
This produces 32-bit float .tif files that are smaller than the .cub files and
are generally more compatible with other software. 8 or 16-bit .tif files can be
produced by changing the output type in gdal_translate in process_nac.sh script
at line 84.

Default export and search area folders are set to use relative paths within this
repository. Git ignores all files in these directories except the .gitkeep files
to prevent accidental commit of image files. Change these variables if you want
to use different folders.

Timeouts are set to 360 seconds (6 minutes) for processing each NAC image. If
you have a slow computer or are processing large images like mosaics, you may
want to increase this.
"""

USER_DEM = 'true'
DEM_PATH = Path.cwd().parent / "LunarDEMs" / "SLDEM.demprep.cub"
PERFORM_PHOTOMET = 'false'
CONVERT_TO_TIF = 'true'
EXPORT_FOLDER = Path("export")
AREA_FOLDER = Path("search_areas")
TIMEOUT = 360 # seconds


def parse_quickmap_geojson(
    geojson_file: str | Path,
        inc_range: list | None = None,
        res_range: list | None = None,
        ) -> tuple:
    """
    Parses geojson from quickmap and returns image names and urls

    Args:
        geojson_file (Path): Path to geojson file to parse.
        inc_range (list | None): Optional list of two floats defining the desired range of solar incidence angles.
        res_range (list | None): Optional list of two floats defining the desired range of image resolutions.
    Returns:
        tuple: A tuple containing three lists:
            - img_names: List of image names.
            - lroc_links: List of LROC image URLs.
            - missing_links: List of image names with missing URLs.
    """
    # Instantiate dict and missing list
    img_names = []
    lroc_links = []
    missing_links = []
    with open(geojson_file,'r') as quickmap_list:

        # Parse geojson file
        data = json.load(quickmap_list)
        print(f"Number of features listed: {len(data['features'])}")
        for i in data['features']:
            img_name = i['properties']['Image']

            # Check if solar incidence is within desired range if defined
            if inc_range is not None:
                if not (inc_range[0] <= (i['properties']['Incidence']) <= inc_range[1]):
                    print(f"{img_name} outside incidence range")
                    break

            # Check if resolution is within desired range if defined
            if res_range is not None:
                if not (res_range[0] <= (i['properties']['Resolution']) <= res_range[1]):
                    print(f"{img_name} outside resolution range")
                    break

            # Add to data
            img_url = i['properties']['Url']
            if img_url != '':
                img_names.append(img_name)
                lroc_links.append(img_url)
            else:
                missing_links.append(img_name)

    return img_names, lroc_links, missing_links

def get_nac_meta(name:str, target_url:str) -> dict:
    """
    Scrapes data from LROC NAC image website for use in processing

    Args:
        name (str): Name of the file to save the NAC image as.
        target_url (str): URL of the LROC page containing the NAC image link.
    returns:
        dict: Dictionary containing metadata and links for the NAC image.
    """
    # Open lroc url for parsing
    res = requests.get(target_url)
    soup = BeautifulSoup(res.content, 'html.parser')

    # Create dataframe to store metadata
    meta = {'Name':name, 'LROC url':target_url}

    # Grab relevant links (at top of table)
    for link in soup.find_all('a'):
        href: str = str(link.get('href'))
        if 'EDR' in href and '.IMG' in href:
            meta['EDR url'] = 'https:' + href
        if '.IMG' not in href and '.tif' not in href:
            meta['Pair url'] = 'https:' + href

    # Parse image meta data from table on lroc website
    table = soup.find('table')
    i = 0 # loop counter to skip first loop (links in different format)
    for row in table.find_all('tr'):
        if i > 0:
            columns = row.find('td')
            # Remove extra newlines
            row_as_list = [column.text for column in columns if column.text != '\n']
            # Add to df
            meta[row_as_list[0]] = row_as_list[1]
        i = i + 1

    # Check for crosstrack summing
    if meta['Line samples'] == 2532:
        meta['Crosstrack summing'] = 'true'
    else:
        meta['Crosstrack summing'] = 'false'

    # Determine if lronacpho or photomet is better for photometric correction
    if 15 < float(meta['Phase angle']) < 65 and float(meta['Incidence angle']) < 60:
        meta['Use lronacpho'] = 'true'
    else:
        meta['Use lronacpho'] = 'false'

    return meta

def download_edr_via_requests(nac_name: str, nac_url: str) -> str:
    """
    UNUSED: fails to handle pds redirect correctly, results in 404

    Utilizes requests package. Error may be related to %0a added to end of url
    for unknown reason?
    """
    ## Set export
    #export_name = nac_name + '.IMG'
    #export_path = Path("temp") / export_name
    ## Set fail log
    #export_fail_file = nac_name + '_fail.log'
    #export_fail_path = Path("temp") / export_fail_file
    ## Get image from url
    #img_data = requests.get(nac_url)
    #if img_data.status_code == 200:
    #    with open(Path("temp") / export_name, 'wb') as f:
    #        f.write(img_data.content)
    #        print(f"NAC saved in temp folder as {export_name}")
    #        return export_path
    #else:
    #    print(f"get edr unsuccessful: {img_data.status_code}")
    #    with open(Path("temp") / export_fail_file, 'wb') as f:
    #                f.write(img_data.content)
    #                print(img_data.url)
    #                print(f"Fail log saved in temp folder as {export_fail_file}")
    #    return export_fail_path
    return 'requests_fail'

def download_edr_via_urllib(nac_name: str, nac_url: str) -> float:
    """
    Downloads NAC EDR from provided link and saves into temp folder

    Args:
        nac_name (str): Name of the file to save the NAC image as.
        nac_url (str): URL of the NAC EDR image to download.
    """
    # Track time to download file
    start = time.time()

    # Save image from url
    export_name = nac_name + '.IMG'
    export_path = Path("temp") / export_name
    if not export_path.exists():
        urllib.request.urlretrieve(nac_url, export_path)
    else:
        print("EDR file already present")

    # Check download time
    end = time.time()
    download_time = end - start
    return download_time

def process_nac(nac_meta: dict, export_name: str) -> float:
    """
    Uses conda ISIS environment to run bash script to process NAC EDR into .cub

    Args:
        nac_meta (dict): Dictionary containing metadata and links for the NAC image.
        export_name (str): Name of the file to save the processed NAC image as.
    Returns:
        tuple: A tuple containing the export name of the processed NAC image and the processing time in seconds.
    """
    # Track processing time
    start = time.time()

    # Set variables for bash script
    edr_file = nac_meta['Product']
    patch_size = str(round(100 / float(nac_meta['Resolution'])))
    temp_dir = Path.cwd() / "temp"
    bash_command = [
        'bash',
        'src/process_nac.sh',
        edr_file,                       # $1 EDR name
        nac_meta['Crosstrack summing'], # $2 crosstrack summing?
        PERFORM_PHOTOMET,               # $3 perform photometric correction?
        nac_meta['Use lronacpho'],      # $4 use lronacpho for above?
        nac_meta['Center longitude'],   # $5 center longitude
        nac_meta['Center latitude'],    # $6 center latitude
        patch_size,                     # $7 dem scale / resolution
        CONVERT_TO_TIF,                 # $8 if want tif
        temp_dir,                       # $9 working directory
        USER_DEM,                       # $10 if user dem
        DEM_PATH                        # $11 dem path
    ]

    # Start process
    try:
        subprocess.run(bash_command,
                       check=True,
                       capture_output=True,
                       text=True,
                       timeout=TIMEOUT)
    except subprocess.TimeoutExpired as e:
        raise TimeoutError(f"Processing timed out for {nac_meta['Product']}. "
                           "Try processing manually.")

    ## Pipe for debugging
    #with subprocess.Popen(bash_command, stdout=subprocess.PIPE, text=True) as process:
    #    # Read and print line-by-line as it streams
    #    for line in process.stdout:
    #        print(line, end='')  # end='' prevents double line break

    # Move final image from temp to export
    temp_path = Path("temp") / export_name
    if temp_path.exists():
        shutil.move(temp_path, EXPORT_FOLDER / export_name)
        src.utils.clear_directory("temp")
    else:
        raise FileNotFoundError(f"Processed file {export_name} not found in temp folder")

    # Check processing time
    end = time.time()
    process_time = end - start

    return process_time

def process_search_area() -> None:
    """
    Main function to process NAC images from a selected Quickmap geojson file.
    
    Args:
        None
    """

    # Ask which geojson to process
    area_file = src.utils.ask_which_file(AREA_FOLDER, '.geojson', "Select which Quickmap geojson to process")
    area_path = AREA_FOLDER / area_file
    area = area_file.replace('.geojson', '')

    # Set log names
    processed_log = Path("logs") / (area + '_processed.json')
    missing_log = Path("logs") / (area + '_missing.log')
    
    # Parse geojson for nac names and urls
    names, links, missing = parse_quickmap_geojson(area_path)

    # Log missing image urls
    if missing != []:
        print(f'Some images missing urls, check {missing_log}')
        with open(missing_log, 'w') as f:
            for i, e in enumerate(missing):
                f.write(missing[i] + ',')

    # Cancel if no links found in geojson
    if links == []:
        print(f"No urls found in geojson, check for {missing_log} or double check geojson")
        return

    # Get metadata, download, and process
    performance = {} # Log performance for each nac
    fails = []
    for i in trange(len(names), desc="Processing NAC images", unit="image", leave=True):

        # Get download link and metadata from LROC website
        nac_meta = get_nac_meta(names[i], links[i])

        # Use USGS ISIS to process NAC into usable format
        export_name = ''
        if CONVERT_TO_TIF:
            export_name = nac_meta['Product'].replace('E', '.tif')
        else:
            export_name = nac_meta['Product'].replace('E', '.cub')
    
        # Check if file already exists in export folder
        if (EXPORT_FOLDER / export_name).exists():
            with open(processed_log, 'a') as log:
                log.write(f"{export_name} already exists in export folder, skipping...\n")
            print(f"{export_name} already exists in export folder, skipping...")
            continue

        # Download EDR
        print(f'Downloading EDR for {names[i]}')
        try:
            download_time = download_edr_via_urllib(nac_meta['Product'],
                                                    nac_meta['EDR url'])
            print(f"Download time: {download_time} seconds")
        except Exception as e:
            print(f"Download failed, check {processed_log}")
            fails.append(f'Failed to download EDR: {e}')
            download_time = None
            continue

        # Process EDR
        print(f'Processing {nac_meta["Product"]}')
        try:
            process_time = process_nac(nac_meta, export_name)
            print(f"NAC processed, {export_name} available in export folder.")
            print(f"Processing time: {process_time} seconds")
        except Exception as e:
            print(f"Processing failed, check {processed_log}")
            fails.append(f'Failed to process: {e}')
            process_time = None
            continue

        # Append to temporary log in case process is interrupted
        with open(processed_log, 'a') as log:
            log.write(f"{names[i]}: {export_name},"
                      f"download time: {download_time},"
                      f"process time: {process_time}\n")
            log.write(f"Fails: {fails}\n")

        
        performance[names[i]] = {'download_time': download_time,
                                   'process_time': process_time}

    # Log performance
    download_times = []
    process_times = []
    for x in performance:
        download_times.append(performance[x]['download_time'])
        process_times.append(performance[x]['process_time'])

    # Make sure there are valid download and process times before calculating totals and averages
    if download_times and process_times:
        # Calculate total and average times
        total_dl_time = sum(download_times)
        total_pr_time = sum(process_times)
        total_time = total_dl_time + total_pr_time
        avg_dl_time = total_dl_time / len(download_times)
        avg_pr_time = total_pr_time / len(process_times)

        # Add to performance dict
        performance['all together'] = {
            'total_dl_time': total_dl_time,
            'total_pr_time': total_pr_time,
            'total_time': total_time,
            'avg_dl_time': avg_dl_time,
            'avg_pr_time': avg_pr_time,
            'fails': fails
        }

        # Write performance to log file in JSON format
        with open(processed_log, 'w') as log:
            log.write(json.dumps(performance, indent=4))

    return
