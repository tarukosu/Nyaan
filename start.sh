#!/bin/bash
export PATH="/home/pi/miniconda3/bin:$PATH"
source activate nyaan
cd $(dirname $0)
python ./scripts/nyaan.py



