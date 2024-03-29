#!/usr/bin/env python3
# MESI CC Protocol
import os.path
import json
from os import path
import mesi_cache as cache
import sys

def json_dump(filepath, dict):

    with open(filepath, 'w', encoding='utf-8') as file_obj:
        json.dump(dict, file_obj, ensure_ascii=False, indent=2)

# Main
if __name__ == "__main__":

    # open inst file
    inst_dict   = json.loads(sys.argv[1])
    #inst_dict   = json.load(inst_file)
    reset       = inst_dict["reset"]
    num_cache   = inst_dict["num_cache"]
    cache_type  = inst_dict["cache_type"]
    cache_size  = inst_dict["cache_size"]
    line_size   = inst_dict["line_size"]
    mem_size    = inst_dict["mem_size"]
    cache_way   = inst_dict["cache_way"]
    run_node    = inst_dict["run_node"]
    node_inst   = {}
    for i in range(num_cache):
        node_inst[i] = inst_dict[f"node_{i}"]


    # open cache file
    # if len(sys.argv) == 3 and reset == 1:
    #     os.remove(sys.argv[2])
    if len(sys.argv) == 3:
        cache_dict = json.loads(sys.argv[2])
        #cache_dict = json.load(cache_file)
    else:
        cache_dict = None

    
    # Create caches
    cache_list = []
    if cache_type == "d":
        for i in range(num_cache):
            if cache_dict != None:
                cache_list.append(cache.direct_cache(i, cache_size, line_size, mem_size, cache_dict[str(i)]["cache"], cache_dict[str(i)]["LSR"], cache_dict[str(i)]["PC"]))
            else:
                cache_list.append(cache.direct_cache(i, cache_size, line_size, mem_size, None, [], 0))
    elif cache_type == "f":
        for i in range(num_cache):
            if cache_dict != None:
                cache_list.append(cache.fully_cache(i, cache_size, line_size, mem_size, cache_dict[str(i)]["cache"], cache_dict[str(i)]["LSR"], cache_dict[str(i)]["PC"]))
            else:
                cache_list.append(cache.fully_cache(i, cache_size, line_size, mem_size, None, [], 0))
    else:
        for i in range(num_cache):
            if cache_dict != None:
                cache_list.append(cache.nway_cache(i, cache_size, line_size, mem_size, cache_way, cache_dict[str(i)]["cache"], cache_dict[str(i)]["LSR"], cache_dict[str(i)]["PC"]))
            else:
                cache_list.append(cache.nway_cache(i, cache_size, line_size, mem_size, cache_way, None, [], 0))


    k = node_inst[run_node][cache_list[run_node].PC]
    # Bus operation
    bus_reply = []
    bus_info = cache_list[run_node].cache_operation(k[0], k[1])
    #print(bus_info["bus_info"])
    for i in cache_list:
        if i.cache_ID != run_node:
            bus_reply.append(i.bus_operation(bus_info["bus_info"], k[1])["bus_reply"])
    #print(bus_reply)

    # Change from E to S
    if bus_info["bus_info"] == "BusRd" and True in bus_reply:
        cache_list[run_node].cache_dict[bus_info["dict_key"]]["protocol"] = "S"
    
    # PC + 1
    cache_list[run_node].PC = cache_list[run_node].PC + 1

    # for node, inst_list in node_inst.items():
    #     for k in inst_list:
    #         # Bus operation
    #         bus_reply = []
    #         bus_info = cache_list[node].cache_operation(k[0], k[1])
    #         print(bus_info["bus_info"])
    #         for i in cache_list:
    #             if i.cache_ID != node:
    #                 bus_reply.append(i.bus_operation(bus_info["bus_info"], k[1])["bus_reply"])
    #                 print(bus_reply)

    #         # Change from E to S
    #         if bus_info["bus_info"] == "BusRd" and True in bus_reply:
    #             cache_list[node].cache_dict[bus_info["dict_key"]]["protocol"] = "S"

    # Print out cache for debug
    # for i in cache_list:
    #     i.print_cache()

    # Dump ot cache json file
    dump_dict = {}
    for i in cache_list:
        dump_dict.update(i.return_cache_dict())
    json_dump("cache.json", dump_dict)

    total_dict = {"inst": inst_dict, "cache": dump_dict}
    print(json.dumps(total_dict, indent=2))
    # print(json.dumps(inst_dict, indent=2))
    # print(json.dumps(dump_dict, indent=2))
