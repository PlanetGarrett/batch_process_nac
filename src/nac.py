import json
import subprocess
import requests
from bs4 import BeautifulSoup
import os
import urllib.request
import time
import shutil
import src.utils

"""
Functions for downloading and processing LROC NAC images listed in Quickmap geojson files.

If you want to use a user-provided DEM for processing, set USER_DEM to 'true'.
Set DEM_PATH to the path of the DEM to use for processing.
If you want to perform photometric correction, set PERFORM_PHOTOMET to 'true'.
If you want to convert the output to .tif format, set CONVERT_TO_TIF to 'true'.
"""

USER_DEM = 'true'
DEM_PATH = "/home/scorn/Documents/LunarDEMs/SLDEM.demprep.cub"
PERFORM_PHOTOMET = 'false'
CONVERT_TO_TIF = 'true'
EXPORT_FOLDER  = "/home/scorn/Documents/Nacs"
AREA_FOLDER = "/home/scorn/Documents/SearchAreas"


def parse_quickmap_geojson(
        geojson_file: str,
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
        print(len(data['features']))
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
    #export_path = os.path.join("temp", export_name)
    ## Set fail log
    #export_fail_file = nac_name + '_fail.log'
    #export_fail_path = os.path.join("temp", export_fail_file)
    ## Get image from url
    #img_data = requests.get(nac_url)
    #if img_data.status_code == 200:
    #    with open(os.path.join("temp", export_name), 'wb') as f:
    #        f.write(img_data.content)
    #        print(f"NAC saved in temp folder as {export_name}")
    #        return export_path
    #else:
    #    print(f"get edr unsuccessful: {img_data.status_code}")
    #    with open(os.path.join("temp", export_fail_file), 'wb') as f:
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
    export_path = os.path.join("temp", export_name)
    if not os.path.exists(export_path):
        urllib.request.urlretrieve(nac_url, export_path)
    else:
        print("EDR file already present")

    # Check download time
    end = time.time()
    download_time = end - start
    return download_time

def process_nac(nac_meta: dict) -> tuple:
    """
    Uses conda ISIS environment to run bash script to process NAC EDR into .cub

    Args:
        nac_meta (dict): Dictionary containing metadata and links for the NAC image.
    Returns:
        tuple: A tuple containing the export name of the processed NAC image and the processing time in seconds.
    """
    # Track processing time
    start = time.time()

    # Use USGS ISIS to process NAC into usable format
    if CONVERT_TO_TIF:
        export_name = nac_meta['Product'].replace('E', '.tif')
    else:
        export_name = nac_meta['Product'].replace('E', '.cub')

    # Check if file already exists in export folder
    if os.path.exists(os.path.join(EXPORT_FOLDER, export_name)):
        print(f"{export_name} already exists in export folder, skipping...")
        return export_name, 0.0

    # Set variables for bash script
    edr_file = nac_meta['Product']
    patch_size = str(round(100 / float(nac_meta['Resolution'])))
    temp_dir = os.path.join(os.getcwd(), "temp")
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

    # Start the process with a pipe for standard output
    with subprocess.Popen(bash_command, stdout=subprocess.PIPE, text=True) as process:
        # Read and print line-by-line as it streams
        for line in process.stdout:
            print(line, end='')  # end='' prevents double line break

    # Move final image from temp to export
    shutil.move(os.path.join("temp", export_name), os.path.join(EXPORT_FOLDER, export_name))
    src.utils.clear_directory("temp")

    # Check processing time
    end = time.time()
    process_time = end - start

    return export_name, process_time

def process_search_area() -> None:
    """
    Main function to process NAC images from a selected Quickmap geojson file.
    
    Args:
        None
    """

    # Ask which geojson to process
    area_file = src.utils.ask_which_file(AREA_FOLDER, '.geojson', "Select which Quickmap geojson to process")
    area_path = os.path.join(AREA_FOLDER, area_file)
    area = area_file.replace('.geojson', '')

    # Set log names
    processed_log = os.path.join("logs", area + '_processed.json')
    missing_log = os.path.join("logs", area + '_missing.log')
    
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
    for i, nac in enumerate(names):

        # Get download link and metadata from LROC website
        nac_meta = get_nac_meta(names[i], links[i])

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
            export_name, process_time = process_nac(nac_meta)
            print(f"NAC processed, {export_name} available in export folder.")
            print(f"Processing time: {process_time} seconds")
        except Exception as e:
            print(f"Processing failed, check {processed_log}")
            fails.append(f'Failed to process: {e}')
            process_time = None
            continue

        # Append to temporary log in case process is interrupted
        with open(processed_log, 'a') as log:
            log.write(f"{names[i]}: {export_name}, download time: {download_time}, process time: {process_time}\n")
        performance[names[i]] = {'download_time': download_time,
                                   'process_time': process_time}

    # Log performance
    download_times = []
    process_times = []
    for x in performance:
        download_times.append(performance[x]['download_time'])
        process_times.append(performance[x]['process_time'])
    total_dl_time = sum(download_times)
    total_pr_time = sum(process_times)
    total_time = total_dl_time + total_pr_time
    avg_dl_time = total_dl_time / len(download_times)
    avg_pr_time = total_pr_time / len(process_times)

    performance['all together'] = {
        'total_dl_time': total_dl_time,
        'total_pr_time': total_pr_time,
        'total_time': total_time,
        'avg_dl_time': avg_dl_time,
        'avg_pr_time': avg_pr_time,
        'fails': fails
    }

    with open(processed_log, 'w') as log:
        log.write(json.dumps(performance, indent=4))

    return
