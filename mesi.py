# MESI CC Protocol
import os.path
import json
from os import path
import mesi_cache as cache

def json_dump(filepath, dict):

    with open(filepath, 'w', encoding='utf-8') as file_obj:
        json.dump(dict, file_obj, ensure_ascii=False, indent=2)

# Main
if __name__ == "__main__":

    # open cache file
    if path.exists("cache.json"):
        cache_file = open("cache.json", 'r')
        cache_dict = json.load(cache_file)
    else:
        cache_dict = None

    # open inst file
    if path.exists("inst.json"):
        inst_file   = open("inst.json", 'r')
        inst_dict   = json.load(inst_file)
        num_cache   = inst_dict["num_cache"]
        cache_ID    = inst_dict["cache_ID"]
        cache_type  = inst_dict["cache_type"]
        cache_way   = inst_dict["cache_way"]
        inst        = inst_dict["inst"]
        addr        = inst_dict["addr"]
    else:
        inst_dict = None
    
    # Create caches
    cache_list = []
    if cache_type == "d":
        for i in range(num_cache):
            if cache_dict != None:
                cache_list.append(cache.direct_cache(i, file = cache_dict[str(i)]))
            else:
                cache_list.append(cache.direct_cache(i))
    elif cache_type == "f":
        for i in range(num_cache):
            if cache_dict != None:
                cache_list.append(cache.fully_cache(i, file = cache_dict[str(i)]))
            else:
                cache_list.append(cache.fully_cache(i))
    else:
        for i in range(num_cache):
            if cache_dict != None:
                cache_list.append(cache.nway_cache(i, file = cache_dict[str(i)], way = cache_way))
            else:
                cache_list.append(cache.nawy_cache(i, way = cache_way))

    # Bus operation
    bus_reply = []
    bus_info = cache_list[cache_ID].cache_operation(inst, addr)
    print(bus_info["bus_info"])
    for i in cache_list:
        if i.cache_ID != cache_ID:
            bus_reply.append(i.bus_operation(bus_info["bus_info"], addr)["bus_reply"])
            print(bus_reply)

    # Change from E to S
    if bus_info["bus_info"] == "BusRd" and True in bus_reply:
        cache_list[cache_ID].cache_dict[bus_info["dict_key"]]["protocol"] = "S"

    # Print out cache for debug
    for i in cache_list:
        i.print_cache()

    # Dump ot cache json file
    dump_dict = {}
    for i in cache_list:
        dump_dict.update(i.return_cache_dict())
    json_dump("cache.json", dump_dict)
