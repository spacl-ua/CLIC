#!/usr/bin/env python3

import os
from glob import glob

bytes = 0

for filename in glob('valid_encoded/*.jpg'):
	bytes += os.stat(filename).st_size

print(bytes)
