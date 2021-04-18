#!/usr/bin/env python3
from MSI_snoop_cache import direct_cache
from MSI_snoop_cache import fully_cache
from MSI_snoop_cache import nway_cache
from MSI_snoop_bus import bus
import os.path
import json
import sys
from os import path


def json_dump(filepath, dict):
    with open(filepath, 'w', encoding='utf-8') as file_obj:
        json.dump(dict, file_obj, ensure_ascii=False, indent=2)


# Main
def main():
    shared_bus = bus()
    #inst_file   = open(sys.argv[1], 'r')
    #inst_dict   = json.load(inst_file)
    inst_dict   = json.loads(sys.agv[1])
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

    if len(sys.argv) == 3:
        #cache_file = open(sys.argv[2], 'r')
        #cache_dict = json.load(cache_file)
        cache_dict  = json.loads(sys.argv[2])
    else:
        cache_dict = None

    cache_list = []
    if cache_type == "d":
        for i in range(num_cache):
            if cache_dict != None:
                cache_list.append(direct_cache(i, cache_size, line_size, mem_size, shared_bus,
                                                 cache_dict[str(i)]["cache"], cache_dict[str(i)]["LSR"], cache_dict[str(i)]["PC"]))
            else:
                cache_list.append(direct_cache(i, cache_size, line_size, mem_size, shared_bus, None, [], 0))
    elif cache_type == "f":
        for i in range(num_cache):
            if cache_dict != None:
                cache_list.append(fully_cache(i, cache_size, line_size, mem_size, shared_bus,
                                                cache_dict[str(i)]["cache"], cache_dict[str(i)]["LSR"], cache_dict[str(i)]["PC"]))
            else:
                cache_list.append(fully_cache(i, cache_size, line_size, mem_size, shared_bus, None, [], 0))
    else:
        for i in range(num_cache):
            if cache_dict != None:
                cache_list.append(nway_cache(i, cache_size, line_size, mem_size, cache_way, shared_bus,
                                             cache_dict[str(i)]["cache"], cache_dict[str(i)]["LSR"], cache_dict[str(i)]["PC"]))
            else:
                cache_list.append(nway_cache(i, cache_size, line_size, mem_size, cache_way, shared_bus, None, [], 0))

    k = node_inst[run_node][cache_list[run_node].PC]
    # Bus operation
    bus_reply = []
    if k[0] == "st":
        cache_list[run_node].write(k[1])
    else:
        cache_list[run_node].read(k[1])

    #cache_list[0].write(66, 67)
    #cache_list[0].read(66)
    #cache_list[1].read(66)

    cache_list[run_node].PC = cache_list[run_node].PC + 1

    dump_dict = {}
    for i in cache_list:
        dump_dict.update(i.return_cache_dict())
    json_dump("cache.json", dump_dict)

    total_dict = {"inst": inst_dict, "cache": dump_dict}
    print(json.dumps(total_dict, indent=2))

    #processors = 4
    #caches = []
    #for cache_id in range(processors):
    #    this_cache = direct_cache(cache_id)
    #    caches.append(this_cache)
    #c = direct_cache(0)
    #a = direct_cache(1)
    #c = direct_cache(0)
    #c = direct_cache(0)
    #print(c.operation("st", 66, 45))
    #print(c.write(66, 45))
    #print(c.operation("st", 332, 40))
    #print(c.operation("st", 167, 57))
    #print(c.write(66, 67))
    #print(c.read(66))
    #print(a.read(66))
    #c.print_cache()
    #a.print_cache()
    #print(caches[0])

if __name__ == "__main__":
	main()