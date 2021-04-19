#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import mpsys_dir as mpd
import json
from os import path
import sys

def json_dump(filepath, dict):
    with open(filepath, 'w', encoding='utf-8') as file_obj:
        json.dump(dict, file_obj, ensure_ascii=False, indent=2)

# Main
if __name__ == "__main__":
    # open inst file
    inst_dict = json.loads(sys.argv[1])

    # open cache file
    if len(sys.argv) == 3:
        cache_dict_in = json.loads(sys.argv[2])
    else:
        cache_dict_in = None

    # Simulation Starts
    print_flag = False
    mpsys = mpd.mpsys_dir(inst_dict, print_flag)
    #if inst_dict["reset"] == 0:
    #    pass
    #else:
    if cache_dict_in != None:
        mpsys.update_dict(cache_dict_in)
    mpsys.run_cycle()

    # Output cache.json
    cache_dict_out = mpsys.output_dict()
    json_dump("./cache.json", cache_dict_out)

    # Output to Web
    dict_to_web = {"inst": inst_dict, "cache":cache_dict_out}
    print(json.dumps(dict_to_web, indent=2))
