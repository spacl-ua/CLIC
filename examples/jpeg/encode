#!/bin/bash

for f in ~/Downloads/test*/*.png; do
	if [ $(python file_size.py) -lt 15749090 ]; then break; fi
	convert "$f" -sampling-factor "4:2:0" -quality 6 "images/$(basename ${f/.png/.jpg})";
done
