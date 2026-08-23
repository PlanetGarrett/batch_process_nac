# Bath Process NAC

A simple set of Python and shell tools for batch processing LRO NAC images into
projected, dem-corrected images for use in GIS applications.

## Installation

```bash
git clone https://github.com/PlanetGarrett/batch_process_nac.git
```

## Requirements

- Linux OS or WLS
- USGS ISIS 3 installed via Miniforge
- ISIS base data and lro calibration data (spice via web option to conserve space)
- Python 3.7+
- bs4 (BeautifulSoup)
- requests
- Internet connection to download NAC EDRs

## Usage

This repository is not set to run from command line due to the user-specific
file paths required. Could be refactored to ask user for configuration, but
currently beyond scope.

### I. Verify USGS ISIS functioning for NAC images

Verify ISIS is installed and working, you can test an individually downloaded
NAC such as the one below.

https://data.lroc.im-ldi.com/lroc/view_lroc/LRO-L-LROC-3-CDR-V1.0/M192559876LC

Visit these websites for more information on installing and using ISIS

https://isis.astrogeology.usgs.gov/7.0.0/UserStart/index.html

https://github.com/DOI-USGS/ISIS3#installation

Make sure the conda environment can be activated via "isis" or change line 26
of the process_nac.sh to use the name of yours (e.g. isis10.0.0 for example).

### II. Get geojson list of NAC images from LROC Quickmap

Go to https://quickmap.lroc.im-ldi.com and select an area using the built in
feature tools. On the right side, click on products and then select NAC. You
should see a list of NAC images available for your selected feature location.
Use the button at the bottom to export the list
as a geojson file. Rename the downloaded file if desired and place in the
"search_areas" subdirectory here.

### III. Set constants in nac.py

src/nac.py contains constants to configure how process_nac.sh functions and set
appropriate directory paths. Make sure to set these to fit your needs. Note that
these use strings instead of booleans for compatibility with the Bash shell.

Most importantly the ISIS processing performed will use a lunar DEM to correct
NAC images. If you want to conserve space, set USER_DEM to anything other than
'true'.

Setting USER_DEM to true requires a locally stored DEM. Accuracy can be improved
by using other shape models such as the “WAC GLD 100 Topography” (about 12 gb
size) available at:
https://lroc.im-ldi.com/data/support/popular_downloads/WAC_GLD100_V1.0_GLOBAL_with_LOLA_30M_POLE.16bit.lp.demprep.zip

If you want better accuracy and are using NACs between +-60 degrees latitude,
you can follow the instructions in sldem_preprocess/sldem.py to produce a
60 m/pixel shapemodel (43 gb final file size).

See the guide in Acknowledgements for more information on polar-region NAC
images or using NAC DTMs. Adapting these scripts to use these may require some
additional work.

### IV. Run main.py

Processing and downloading time will vary based on your system resources.
Check the logs to see average times and any errors. You can use the included
single_test.geojson in the tests directory to make sure it works correctly.

Any processes that timeout or otherwise fail will be added to the "\_processed"
.json log under fails. You can try to run the area again (it will check for any
.tifs/.cubs that are already processed in the export folder and skip those) or
you may need to process them manually. In most cases however, it appears to be
caused by images with high slew angles (oblique views of the surface) which may
require a different processing method.

### V. Move images from export folder

Since the script checks for images that are already processed, it may be helpful
to keep the images in the export folder until you are completely done with all
areas. Processing multiple areas near one another are likely to result in some
duplicate images so this will help cut down on unnecessary processing time. Once
you are done, move the images to where you need them.

## Acknowledgements

This package is only possible because of the thorough instructions from Robert
Wagner and the LROC team. Read the guide via the link below for more information on processing NAC images:

Wagner, R., & LROC Team. (2026). Lunar Reconnaissance Orbiter Narrow Angle Camera Processing Guide (Version 1.1.4) [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.20058490

## License

MIT

## Additional Notes

May extend this project to function for other instruments / missions.
