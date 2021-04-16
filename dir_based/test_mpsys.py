# -*- coding: utf-8 -*-
import mpsys_dir as mpd
import json
from os import path

def json_dump(filepath, dict):
    with open(filepath, 'w', encoding='utf-8') as file_obj:
        json.dump(dict, file_obj, ensure_ascii=False, indent=2)

# Main
if __name__ == "__main__":
    # open inst file
    inst_dict = {}
    if path.exists("inst.json"):
        inst_file   = open("inst.json", 'r')
        inst_dict   = json.load(inst_file)

    # Instantiate Multi-Processor System
    mpsys = mpd.mpsys_dir(inst_dict, True)

    # Simulation Starts
    cycle = 0
    while True:
        cmd = input("Please input command (reset/run/quit): ")

        if cmd == "reset":
            mpsys.reset()
            cycle = 0

            # Output cache.json
            cache_dict = mpsys.output_dict()
            cache_dict["cycle"] = cycle
            json_dump("./cache.json", cache_dict)
        elif cmd == "run":
            proc_sel = input("Please select processor(s) to run (use 'all' for concurrent mode): ")
            mpsys.run_cycle(proc_sel)
            cycle += 1

            # Output cache.json
            cache_dict = mpsys.output_dict()
            cache_dict["cycle"] = cycle
            json_dump("./cache.json", cache_dict)
        elif cmd == "quit":
            break
        else:
            print("Please enter valid command!")
            

    