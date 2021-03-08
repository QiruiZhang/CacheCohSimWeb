from MSI_snoop_cache import cache
from MSI_snoop_bus import bus
import os.path
import json
from os import path


def json_dump(filepath, dict):
    with open(filepath, 'w', encoding='utf-8') as file_obj:
        json.dump(dict, file_obj, ensure_ascii=False, indent=2)


# Main
if __name__ == "__main__":

    # open inst file
    if path.exists("inst.json"):
        inst_file = open("inst.json", 'r')
        inst_dict = json.load(inst_file)
        reset = inst_dict["reset"]
        num_cache = inst_dict["num_cache"]
        cache_ID = inst_dict["cache_ID"]
        cache_type = inst_dict["cache_type"]
        cache_size = inst_dict["cache_size"]
        line_size = inst_dict["line_size"]
        mem_size = inst_dict["mem_size"]
        cache_way = inst_dict["cache_way"]
        inst = inst_dict["inst"]
        addr = inst_dict["addr"]
    else:
        inst_dict = None

    # open cache file
    if path.exists("cache.json"):
        if reset == 1:
            os.remove("cache.json")
    if path.exists("cache.json"):
        cache_file = open("cache.json", 'r')
        cache_dict = json.load(cache_file)
    else:
        cache_dict = None

    # Create caches
    caches = []
    if cache_type == "d":
        for i in range(num_cache):
            if cache_dict != None:
                caches.append(cache.direct_cache(i, cache_size, line_size, mem_size, bus,
                                                 cache_dict[str(i)]["cache"], cache_dict[str(i)]["LSR"]))
            else:
                caches.append(cache.direct_cache(i, cache_size, line_size, mem_size, bus, None, []))
    elif cache_type == "f":
        for i in range(num_cache):
            if cache_dict != None:
                caches.append(cache.fully_cache(i, cache_size, line_size, mem_size, bus,
                                                cache_dict[str(i)]["cache"], cache_dict[str(i)]["LSR"]))
            else:
                caches.append(cache.fully_cache(i, cache_size, line_size, mem_size, bus, None, []))
    else:
        for i in range(num_cache):
            if cache_dict != None:
                caches.append(
                    cache.nway_cache(i, cache_size, line_size, mem_size, cache_way, bus,
                                     cache_dict[str(i)]["cache"], cache_dict[str(i)]["LSR"]))
            else:
                caches.append(cache.nway_cache(i, cache_size, line_size, mem_size, bus, cache_way, None, []))


    # Print out cache for debug
    for i in caches:
        i.print_cache()

    # Dump ot cache json file
    dump_dict = {}
    for i in caches:
        dump_dict.update(i.return_cache_dict())
    json_dump("cache.json", dump_dict)


def main():
    processors = 4
    caches = []
    for cache_id in range(processors):
        cache = direct_cache(cache_id)
        caches.append(cache)
    c = direct_cache(0)
    #print(c.operation("st", 66, 45))
    print(c.write(66, 45))
    print(c.operation("st", 332, 40))
    print(c.operation("st", 167, 57))
    print(c.write(66, 67))
    print(c.read(66))
    c.print_cache()

#if __name__ == "__main__":
#	main()