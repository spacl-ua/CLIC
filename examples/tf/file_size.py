#!/usr/bin/env python3

import os
import glob

byte_count = 0
for f in glob.glob('valid_encoded/*.jpg'):
	byte_count += os.stat(f).st_size
print(byte_count)
