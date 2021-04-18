
#!/bin/bash
reset=$1
if (($reset==1)); then
    #python3.7 ccsim_dir.py inst.json > output_to_web.json
    inst_file=`cat inst.json`
    #./mesi.py "$inst_file" > output_to_web.json
    ./MSI_snoop_simulator.py "$inst_file" > output_to_web.json
else
    #python3.7 ccsim_dir.py inst.json cache.json > output_to_web.json 
    inst_file=`cat inst.json`
    cache_file=`cat cache.json`
    #./mesi.py "$inst_file" "$cache_file" > output_to_web.json
    ./MSI_snoop_simulator.py "$inst_file" "$cache_file" > output_to_web.json
fi 
