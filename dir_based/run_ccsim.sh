#!/bin/bash
reset=$1
if (($reset==1)); then
    python3.7 ccsim_dir.py inst.json > output_to_web.json
else
    python3.7 ccsim_dir.py inst.json cache.json > output_to_web.json 
fi 