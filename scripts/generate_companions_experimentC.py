#!/usr/bin/env python
# Generate companion files

import glob
import os
from os.path import dirname, join, abspath
from ome_model.experimental import Image, create_companion
import logging
import sys
import subprocess
from PIL import Image as PIL_Image

DEBUG = int(os.environ.get("DEBUG", logging.INFO))


BASE_DIRECTORY = join(
    dirname(abspath(dirname(sys.argv[0]))), 'experimentC', 'companions')

CHANNEL_MAPPING = {
    'NCAPD2gfpc272c78': ("DNA", -16711681, "NCAPD2", -1),
    'NCAPD3gfpc16': ("DNA", -16711681, "NCAPD3", -1),
    'NCAPH2gfpc67': ("DNA", -16711681, "NCAPH2", -1),
    'NCAPHgfpc86': ("DNA", -16711681, "NCAPH", -1),
    'SMC4gfpz82z68': ("DNA", -16711681, "SMC4", -1),
    'NCAPH2-GFP-AF594_NCAPH-Halo-STARRED':
        ("NCAPH", -16711681, "NCAPH2", 16711935),
}

folders = [join(BASE_DIRECTORY, x) for x in os.listdir(BASE_DIRECTORY)]
folders = sorted(filter(os.path.isdir, folders))
logging.info("Found %g folders under %s" % (len(folders), BASE_DIRECTORY))

for folder in folders:
    logging.debug("Finding cells under %s" % folder)
    cells = [x for x in glob.glob(folder + "/*") if os.path.isdir(x)]
    for cell in cells:
        rawtiffs = sorted(map(
            os.path.basename, glob.glob("%s/*.tif" % cell)))
        # Each folder contains 2 multi-page TIFFs, one for each channel
        assert len(rawtiffs) == 2

        # Image Dimensions
        img = PIL_Image.open(join(cell, rawtiffs[1]))
        (size_x, size_y) = img.size
        size_z = 0
        while True:
            try:
                img.seek(size_z)
            except EOFError:
                break
            size_z += 1

        # Create 2-channel image
        image = Image(
            os.path.basename(cell), size_x, size_y, size_z, 2, 1,
            order="XYZCT", type="uint16")
        image.data['Pixels']['PhysicalSizeX'] = '20'
        image.data['Pixels']['PhysicalSizeXUnit'] = 'nm'
        image.data['Pixels']['PhysicalSizeY'] = '20'
        image.data['Pixels']['PhysicalSizeYUnit'] = 'nm'
        (n1, c1, n2, c2) = CHANNEL_MAPPING[os.path.basename(folder)]
        image.add_channel(n1, c1)
        image.add_channel(n2, c2)

        for i in range(len(rawtiffs)):
            image.add_tiff("%s/%s" % (
                os.path.basename(cell), rawtiffs[i]), c=i, z=0, t=0, ifd=0,
                planeCount=size_z)
        create_companion(images=[image], out=cell + '.companion.ome')

        # Generate indented XML for readability
        proc = subprocess.Popen(
            ['xmllint', '--format', '-o', cell + '.companion.ome',
             cell + '.companion.ome'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE)
        (output, error_output) = proc.communicate()
