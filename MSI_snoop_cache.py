import math
import random
import json
from MSI_snoop_bus import bus

# state
#   "I": INVALIDED (no permission)
#   "S": SHARED (R permission, clean)
#   "M": MODIFIED (R/W permission, dirty)

class cache():

    def __init__(self, ID, size, line_size, mem_size, bus, file, LSR, PC):
        self.cache_ID = ID
        self.cache_size = size  # Bytes
        self.cache_line_size = line_size  # Bytes
        self.cache_dict = {}
        self.addr_bits = int(math.log2(mem_size))
        self.cache_num_line = int(size / line_size)
        self.bus = bus
        self.bus.add_cache(self)
        self.line_queue = LSR
        self.PC = PC

        if file == None:
            for i in range(self.cache_num_line):
                self.cache_dict[str(i)] = {"addr": None,
                                      "tag": None,
                                      "index": None,
                                      "offset": None,
                                      #"data" : None,
                                      "state": "I"}
        else:
            self.cache_dict = file

    # transfer decimal to binary and pad with zero
    def decimal2binary(self, num, bits):
        binary = bin(num)[2:].zfill(bits)
        return binary

    def print_cache(self):
        for key, val in self.cache_dict.items():
            print(f"line[{key}] = {val}")

    def return_cache_dict(self):
        return {self.cache_ID: {"cache": self.cache_dict, "LSR": self.line_queue, "PC": self.PC}}


# Direct-map
class direct_cache(cache):

    def __init__(self, ID, size=128, line_size=8, mem_size=512, bus=bus(), file=None, LSR=[], PC=0):
        super().__init__(ID, size, line_size, mem_size, bus, file, LSR, PC)

    def operation(self, inst, addr, data):
        hit = False
        tag, index, offset = self.parse_address(addr)

        # Inst = Store or Load
        if inst == "st" or inst == "ld":
            # Hit
            #for key, val in self.cache_dict.items():
            #   if "I" != val["state"] and index == val["index"] and tag == val["tag"]:
            #       hit = True
            if self.cache_dict[str(int(index, 2))]["state"] != "I" and tag == self.cache_dict[str(int(index, 2))]["tag"]:
                hit = True
            # Miss
            if self.cache_dict[str(int(index, 2))]["state"] == "I":
                self.cache_dict[str(int(index, 2))]["addr"] = addr
                self.cache_dict[str(int(index, 2))]["tag"] = tag
                self.cache_dict[str(int(index, 2))]["index"] = index
                self.cache_dict[str(int(index, 2))]["offset"] = offset
                self.cache_dict[str(int(index, 2))]["data"] = data
                self.cache_dict[str(int(index, 2))]["dirty"] = False
                self.cache_dict[str(int(index, 2))]["state"] = "S"
            # Miss and Evict
            if self.cache_dict[str(int(index, 2))]["state"] != "I" and tag != self.cache_dict[str(int(index, 2))]["tag"]:
                self.cache_dict[str(int(index, 2))]["addr"] = addr
                self.cache_dict[str(int(index, 2))]["tag"] = tag
                self.cache_dict[str(int(index, 2))]["index"] = index
                self.cache_dict[str(int(index, 2))]["offset"] = offset
                self.cache_dict[str(int(index, 2))]["data"] = data
                self.cache_dict[str(int(index, 2))]["dirty"] = False
                self.cache_dict[str(int(index, 2))]["state"] = "S"
                #bus.evict

        return hit

    def write(self, addr):
        hit = False
        mem = False
        mem_data = None
        mem_addr = None
        pass_data = None
        tag, index, offset = self.parse_address(addr)
        #state = "M"
        if (self.cache_dict[str(int(index, 2))]["state"] == "M" and
                tag == self.cache_dict[str(int(index, 2))]["tag"]):
            hit = True
            self.cache_dict[str(int(index, 2))]["addr"] = addr
            self.cache_dict[str(int(index, 2))]["offset"] = offset
            #self.cache_dict[str(int(index, 2))]["data"] = data
            #self.cache_dict[int(index, 2)]["dirty"] = True
        #state = "S"
        if (self.cache_dict[str(int(index, 2))]["state"] == "S" and
                tag == self.cache_dict[int(index, 2)]["tag"]):
            hit = True
            pass_data = self.bus.BusInv(self.cache_ID, addr)
            self.cache_dict[str(int(index, 2))]["addr"] = addr
            self.cache_dict[str(int(index, 2))]["offset"] = offset
            #self.cache_dict[str(int(index, 2))]["data"] = data
            self.cache_dict[str(int(index, 2))]["state"] = "M"
        #state = "I"
        if self.cache_dict[str(int(index, 2))]["state"] == "I":
            pass_data = self.bus.BusRdX(self.cache_ID, addr)
            self.cache_dict[str(int(index, 2))]["addr"] = addr
            self.cache_dict[str(int(index, 2))]["tag"] = tag
            self.cache_dict[str(int(index, 2))]["index"] = index
            self.cache_dict[str(int(index, 2))]["offset"] = offset
            #self.cache_dict[str(int(index, 2))]["data"] = data
            self.cache_dict[str(int(index, 2))]["state"] = "M"
        #evict S
        if (self.cache_dict[str(int(index, 2))]["state"] == "S" and
                tag != self.cache_dict[str(int(index, 2))]["tag"]):
            self.cache_dict[str(int(index, 2))]["addr"] = addr
            self.cache_dict[str(int(index, 2))]["tag"] = tag
            self.cache_dict[str(int(index, 2))]["index"] = index
            self.cache_dict[str(int(index, 2))]["offset"] = offset
            #self.cache_dict[str(int(index, 2))]["data"] = data
            self.cache_dict[str(int(index, 2))]["state"] = "M"
        #evict M
        if (self.cache_dict[str(int(index, 2))]["state"] == "M" and
                tag != self.cache_dict[str(int(index, 2))]["tag"]):
            mem = True
            #mem_data = self.cache_dict[str(int(index, 2))]["data"]
            mem_addr = self.cache_dict[str(int(index, 2))]["addr"]
            self.cache_dict[str(int(index, 2))]["addr"] = addr
            self.cache_dict[str(int(index, 2))]["tag"] = tag
            self.cache_dict[str(int(index, 2))]["index"] = index
            self.cache_dict[str(int(index, 2))]["offset"] = offset
            #self.cache_dict[str(int(index, 2))]["data"] = data
            self.cache_dict[str(int(index, 2))]["state"] = "M"
        return hit, mem, mem_data, mem_addr

    def read(self, addr):
        hit = False
        mem = False
        mem_data = None
        pass_data = None
        mem_addr = None
        tag, index, offset = self.parse_address(addr)
        #state = "M"
        if (self.cache_dict[str(int(index, 2))]["state"] == "M" and
                tag == self.cache_dict[str(int(index, 2))]["tag"]):
            hit = True
            self.cache_dict[str(int(index, 2))]["addr"] = addr
            self.cache_dict[str(int(index, 2))]["offset"] = offset
            #self.cache_dict[int(index, 2)]["data"] = data
            #self.cache_dict[int(index, 2)]["dirty"] = True
        #state = "S"
        if (self.cache_dict[str(int(index, 2))]["state"] == "S" and
                tag == self.cache_dict[str(int(index, 2))]["tag"]):
            hit = True
            self.cache_dict[str(int(index, 2))]["addr"] = addr
            self.cache_dict[str(int(index, 2))]["offset"] = offset
            #self.cache_dict[int(index, 2)]["data"] = data
        #state = "I"
        if self.cache_dict[str(int(index, 2))]["state"] == "I":
            pass_data, mem, mem_addr = self.bus.BusRd(self.cache_ID, addr)
            self.cache_dict[str(int(index, 2))]["addr"] = addr
            self.cache_dict[str(int(index, 2))]["tag"] = tag
            self.cache_dict[str(int(index, 2))]["index"] = index
            self.cache_dict[str(int(index, 2))]["offset"] = offset
            #self.cache_dict[str(int(index, 2))]["data"] = pass_data
            self.cache_dict[str(int(index, 2))]["state"] = "S"
            mem_data = pass_data
        # evict S
        if (self.cache_dict[str(int(index, 2))]["state"] == "S" and
                tag != self.cache_dict[str(int(index, 2))]["tag"]):
            pass_data, mem, mem_addr = self.bus.BusRd(self.cache_ID, addr)
            self.cache_dict[str(int(index, 2))]["addr"] = addr
            self.cache_dict[str(int(index, 2))]["tag"] = tag
            self.cache_dict[str(int(index, 2))]["index"] = index
            self.cache_dict[str(int(index, 2))]["offset"] = offset
            #self.cache_dict[str(int(index, 2))]["data"] = pass_data
            #self.cache_dict[int(index, 2)]["state"] = "M"
        # evict M
        if (self.cache_dict[str(int(index, 2))]["state"] == "M" and
                tag != self.cache_dict[str(int(index, 2))]["tag"]):
            pass_data, mem, mem_addr = self.bus.BusRd(self.cache_ID, addr)
            mem = True
            #mem_data = self.cache_dict[str(int(index, 2))]["data"]
            mem_addr = self.cache_dict[str(int(index, 2))]["addr"]
            self.cache_dict[str(int(index, 2))]["addr"] = addr
            self.cache_dict[str(int(index, 2))]["tag"] = tag
            self.cache_dict[str(int(index, 2))]["index"] = index
            self.cache_dict[str(int(index, 2))]["offset"] = offset
            #self.cache_dict[str(int(index, 2))]["data"] = pass_data
            self.cache_dict[str(int(index, 2))]["state"] = "S"
        return hit, mem, mem_data, mem_addr

    def handle_BusInv(self, addr):
        tag, index, offset = self.parse_address(addr)
        valid = False
        BusReply = None
        #self.cache_dict[int(index, 2)]["addr"] = addr
        #self.cache_dict[int(index, 2)]["tag"] = tag
        #self.cache_dict[int(index, 2)]["index"] = index
        #self.cache_dict[int(index, 2)]["offset"] = offset
        if tag == self.cache_dict[str(int(index, 2))]["tag"]:
            self.cache_dict[str(int(index, 2))]["state"] = "I"
            valid = True
            #BusReply = self.cache_dict[str(int(index, 2))]["data"]
        return valid, BusReply

    def handle_BusRd(self, addr):
        tag, index, offset = self.parse_address(addr)
        valid = False
        BusReply = None
        mem = False
        mem_addr = None
        #self.cache_dict[int(index, 2)]["addr"] = addr
        #self.cache_dict[int(index, 2)]["tag"] = tag
        #self.cache_dict[int(index, 2)]["index"] = index
        #self.cache_dict[int(index, 2)]["offset"] = offset
        if (self.cache_dict[str(int(index, 2))]["state"] == "S" and
                tag == self.cache_dict[str(int(index, 2))]["tag"]):
            valid = True
            BusReply = self.cache_dict[int(index, 2)]["data"]
        if (self.cache_dict[str(int(index, 2))]["state"] == "M" and
                tag == self.cache_dict[str(int(index, 2))]["tag"]):
            valid = True
            self.cache_dict[str(int(index, 2))]["state"] = "S"
            BusReply = self.cache_dict[str(int(index, 2))]["data"]
            #mem snarf
            mem = True
            mem_addr = addr
        return valid, BusReply, mem, mem_addr

    def handle_BusRdX(self, addr):
        tag, index, offset = self.parse_address(addr)
        valid = False
        BusReply = None
        if (self.cache_dict[str(int(index, 2))]["state"] == "S" and
                tag == self.cache_dict[str(int(index, 2))]["tag"]):
            valid = True
            #BusReply = self.cache_dict[str(int(index, 2))]["data"]
            self.cache_dict[str(int(index, 2))]["state"] = "I"
        if (self.cache_dict[str(int(index, 2))]["state"] == "M" and
                tag == self.cache_dict[str(int(index, 2))]["tag"]):
            valid = True
            #BusReply = self.cache_dict[str(int(index, 2))]["data"]
            self.cache_dict[str(int(index, 2))]["state"] = "I"
        return valid, BusReply


    def parse_address(self, addr):
        addr_bin = self.decimal2binary(addr, self.addr_bits)

        # Setup tag, index, offset
        index_bit = int(math.log2(self.cache_num_line))
        offset_bit = int(math.log2(self.cache_line_size))
        tag_bit = self.addr_bits - index_bit - offset_bit

        tag = addr_bin[0:tag_bit]
        index = addr_bin[tag_bit:(self.addr_bits - offset_bit)]
        offset = addr_bin[(self.addr_bits - offset_bit):]

        return tag, index, offset

# Fully Associative
class fully_cache(cache):

    def __init__(self, ID, size = 128, line_size = 8, mem_size = 512, bus=bus(), file=None, LSR=[], PC=0):
        super().__init__(ID, size, line_size, mem_size, bus, file, LSR, PC)
        # For LSR
        #self.line_queue = []

    def operation(self, inst, addr):
        hit = False

        # Inst = Store
        if inst == "st" or inst == "ld":
            # Hit
            for key, val in self.cache_dict.items():
                if tag == val["tag"]:
                    hit = True
                    lru_place, fill_place = self.lru_mechanism(hit, key)
            # Miss
            if hit == False:
                hit_place = None
                # Queue is full
                if len(self.line_queue) == self.cache_num_line:
                    lru_place, fill_place = self.lru_mechanism(hit, hit_place)
                    self.cache_dict[lru_place]["addr"] = addr
                    self.cache_dict[lru_place]["tag"] = tag
                    self.cache_dict[lru_place]["index"] = index
                    self.cache_dict[lru_place]["offset"] = offset

                # Queue is not full yet
                else:
                    # Create a random line slot number
                    lru_place, fill_place = self.lru_mechanism(hit, hit_place)
                    self.cache_dict[fill_place]["addr"] = addr
                    self.cache_dict[fill_place]["tag"] = tag
                    self.cache_dict[fill_place]["index"] = index
                    self.cache_dict[fill_place]["offset"] = offset
        return hit

    def write(self, addr):
        hit = False
        mem = False
        mem_data = None
        mem_addr = None
        pass_data = None
        tag, index, offset = self.parse_address(addr)
        for key, val in self.cache_dict.items():
            if (tag == val["tag"] and
                    self.cache_dict[key]["state"] != "I"):
                hit = True
        #state = "M"
                if self.cache_dict[key]["state"] == "M":
                    self.cache_dict[key]["addr"] = addr
                    self.cache_dict[key]["offset"] = offset
                    #self.cache_dict[key]["data"] = data
        #state = "S"
                else:
                    pass_data = self.bus.BusInv(self.cache_ID, addr)
                    self.cache_dict[key]["addr"] = addr
                    self.cache_dict[key]["offset"] = offset
                    #self.cache_dict[key]["data"] = data
                    self.cache_dict[key]["state"] = "M"
                lru_place, fill_place = self.lru_mechanism(hit, key)
        #state = "I"
        if (hit == False and
                len(self.line_queue) != self.cache_num_line):
            hit_place = None
            # Create a random line slot number
            lru_place, fill_place = self.lru_mechanism(hit, hit_place)
            pass_data = self.bus.BusRdX(self.cache_ID, addr)
            self.cache_dict[fill_place]["addr"] = addr
            self.cache_dict[fill_place]["tag"] = tag
            self.cache_dict[fill_place]["index"] = index
            self.cache_dict[fill_place]["offset"] = offset
            #self.cache_dict[fill_place]["data"] = data
            self.cache_dict[fill_place]["state"] = "M"
        elif (hit == False and
                len(self.line_queue) == self.cache_num_line):
            hit_place = None
            lru_place, fill_place = self.lru_mechanism(hit, hit_place)
        # evict S
            if self.cache_dict[lru_place]["state"] == "S":
                self.cache_dict[lru_place]["addr"] = addr
                self.cache_dict[lru_place]["tag"] = tag
                self.cache_dict[lru_place]["index"] = index
                self.cache_dict[lru_place]["offset"] = offset
                #self.cache_dict[lru_place]["data"] = data
                self.cache_dict[lru_place]["state"] = "M"
        # evict M
            elif self.cache_dict[lru_place]["state"] == "M":
                mem = True
                #mem_data = self.cache_dict[lru_place]["data"]
                mem_addr = self.cache_dict[lru_place]["addr"]
                self.cache_dict[lru_place]["addr"] = addr
                self.cache_dict[lru_place]["tag"] = tag
                self.cache_dict[lru_place]["index"] = index
                self.cache_dict[lru_place]["offset"] = offset
                #self.cache_dict[lru_place]["data"] = data
                self.cache_dict[lru_place]["state"] = "M"
        return hit, mem, mem_data, mem_addr

    def read(self, addr):
        hit = False
        mem = False
        mem_data = None
        pass_data = None
        mem_addr = None
        tag, index, offset = self.parse_address(addr)
        for key, val in self.cache_dict.items():
            if (tag == val["tag"] and
                    self.cache_dict[key]["state"] != "I"):
                hit = True
                print(key)
        #state = "M"
                if self.cache_dict[key]["state"] == "M":
                    self.cache_dict[key]["addr"] = addr
                    self.cache_dict[key]["offset"] = offset
        # state = "S"
                else:
                    self.cache_dict[key]["addr"] = addr
                    self.cache_dict[key]["offset"] = offset
                #lru_place, fill_place = self.lru_mechanism(hit, key)
        # state = "I"
        if (hit == False and
                len(self.line_queue) != self.cache_num_line):
            hit_place = None
            # Create a random line slot number
            lru_place, fill_place = self.lru_mechanism(hit, hit_place)
            pass_data, mem, mem_addr = self.bus.BusRd(self.cache_ID, addr)
            self.cache_dict[fill_place]["addr"] = addr
            self.cache_dict[fill_place]["tag"] = tag
            self.cache_dict[fill_place]["index"] = index
            self.cache_dict[fill_place]["offset"] = offset
            #self.cache_dict[fill_place]["data"] = pass_data
            self.cache_dict[fill_place]["state"] = "S"
            mem_data = pass_data
        elif (hit == False and
                len(self.line_queue) == self.cache_num_line):
            hit_place = None
            lru_place, fill_place = self.lru_mechanism(hit, hit_place)
        # evict S
            if self.cache_dict[lru_place]["state"] == "S":
                pass_data, mem, mem_addr = self.bus.BusRd(self.cache_ID, addr)
                self.cache_dict[lru_place]["addr"] = addr
                self.cache_dict[lru_place]["tag"] = tag
                self.cache_dict[lru_place]["index"] = index
                self.cache_dict[lru_place]["offset"] = offset
                #self.cache_dict[lru_place]["data"] = pass_data
        # evict M
            elif self.cache_dict[lru_place]["state"] == "M":
                pass_data, mem, mem_addr = self.bus.BusRd(self.cache_ID, addr)
                mem = True
                #mem_data = self.cache_dict[lru_place]["data"]
                mem_addr = self.cache_dict[lru_place]["addr"]
                self.cache_dict[lru_place]["addr"] = addr
                self.cache_dict[lru_place]["tag"] = tag
                self.cache_dict[lru_place]["index"] = index
                self.cache_dict[lru_place]["offset"] = offset
                #self.cache_dict[lru_place]["data"] = pass_data
                self.cache_dict[lru_place]["state"] = "S"
        return hit, mem, mem_data, mem_addr

    def handle_BusInv(self, addr):
        tag, index, offset = self.parse_address(addr)
        valid = False
        BusReply = None
        for key, val in self.cache_dict.items():
            if (tag == val["tag"] and
                    self.cache_dict[key]["state"] != "I"):
                self.cache_dict[key]["state"] = "I"
                valid = True
                #BusReply = self.cache_dict[key]["data"]
                self.line_queue.remove(key)
        return valid, BusReply

    def handle_BusRd(self, addr):
        tag, index, offset = self.parse_address(addr)
        valid = False
        BusReply = None
        mem = False
        mem_addr = None
        for key, val in self.cache_dict.items():
            if (tag == val["tag"] and
                    self.cache_dict[key]["state"] != "I"):
                #hit = True
                #state = "S"
                if self.cache_dict[key]["state"] == "S":
                    valid = True
                    #BusReply = self.cache_dict[key]["data"]
                # state = "M"
                else:
                    valid = True
                    self.cache_dict[key]["state"] = "S"
                    #BusReply = self.cache_dict[key]["data"]
                    # mem snarf
                    mem = True
                    mem_addr = addr
                    self.cache_dict[key]["addr"] = addr
                    self.cache_dict[key]["offset"] = offset
                #self.line_queue.remove(key)
                #self.line_queue.append(key)
        return valid, BusReply, mem, mem_addr

    def handle_BusRdX(self, addr):
        tag, index, offset = self.parse_address(addr)
        valid = False
        BusReply = None
        for key, val in self.cache_dict.items():
            if (tag == val["tag"] and
                    self.cache_dict[key]["state"] != "I"):
                # state = "S" and "M"
                valid = True
                #BusReply = self.cache_dict[key]["data"]
                self.cache_dict[key]["state"] = "I"
                self.line_queue.remove(key)
        return valid, BusReply

    def lru_mechanism(self, hit, hit_place):
        lru_place = None
        fill_place = None
        if hit:
            self.line_queue.remove(hit_place)
            self.line_queue.append(hit_place)
        if hit == False:
            #Set is full
            if len(self.line_queue) == self.cache_num_line:
                lru_place = self.line_queue[0]
                self.line_queue.append(self.line_queue[0])
                self.line_queue.pop(0)
            #Set is still empty
            else:
                fill_place = str(random.randint(0, self.cache_num_line - 1))
                while (fill_place in self.line_queue):
                    fill_place = str(random.randint(0, self.cache_num_line - 1))
                self.line_queue.append(fill_place)
        return lru_place, fill_place

    def parse_address(self, addr):
        addr_bin = self.decimal2binary(addr, self.addr_bits)
        # Setup tag, index, offset
        index_bit = 0
        offset_bit = int(math.log2(self.cache_line_size))
        tag_bit = self.addr_bits - index_bit - offset_bit

        tag = addr_bin[0:tag_bit]
        index = None
        offset = addr_bin[(self.addr_bits - offset_bit):]
        return tag, index, offset

# N-way Associative
class nway_cache(cache):

    def __init__(self, ID, size = 128, line_size = 8, mem_size = 512, way = 2, bus=bus(), file=None, LSR=[], PC=0):
        super().__init__(ID, size, line_size, mem_size, bus, file, LSR, PC)
        self.way = way
        # For LSR
        #self.line_queue = []
        if len(LSR) == 0:
            for i in range(int(self.cache_num_line/self.way)):
                list_temp = []
                self.line_queue.append(list_temp)


    def operation(self, inst, addr):
        hit = False
        # Inst = Store or Load
        if inst == "st" or inst == "ld":
            # Hit
            for key, val in self.cache_dict.items():
                if index == val["index"] and tag == val["tag"]:
                    hit = True
                    self.line_queue[int(index, 2)].remove(key)
                    self.line_queue[int(index, 2)].append(key)
            # Miss
            if hit == False:
                # Queue is full
                if len(self.line_queue[int(index, 2)]) == self.way:
                    self.cache_dict[self.line_queue[int(index, 2)][0]]["addr"]   = addr
                    self.cache_dict[self.line_queue[int(index, 2)][0]]["tag"]    = tag
                    self.cache_dict[self.line_queue[int(index, 2)][0]]["index"]  = index
                    self.cache_dict[self.line_queue[int(index, 2)][0]]["offset"] = offset
                    self.line_queue[int(index, 2)].append(self.line_queue[int(index, 2)][0])
                    self.line_queue[int(index, 2)].pop(0)

                # Queue is not full yet
                else:
                    # Create a random line slot number
                    num = random.randint((int(index, 2) * self.way), (int(index, 2) * self.way) + self.way - 1)
                    while (num in self.line_queue[int(index, 2)]):
                        num = random.randint((int(index, 2) * self.way), (int(index, 2) * self.way) + self.way - 1)

                    self.cache_dict[num]["addr"]   = addr
                    self.cache_dict[num]["tag"]    = tag
                    self.cache_dict[num]["index"]  = index
                    self.cache_dict[num]["offset"] = offset
                    self.line_queue[int(index, 2)].append(num)
        return hit

    def write(self, addr):
        hit = False
        mem = False
        mem_data = None
        mem_addr = None
        pass_data = None
        tag, index, offset = self.parse_address(addr)
        for key, val in self.cache_dict.items():
            if (tag == val["tag"] and
                    index == val["index"] and
                    self.cache_dict[key]["state"] != "I"):
                hit = True
        #state = "M"
                if self.cache_dict[key]["state"] == "M":
                    self.cache_dict[key]["addr"] = addr
                    self.cache_dict[key]["offset"] = offset
                    #self.cache_dict[key]["data"] = data
        #state = "S"
                else:
                    pass_data = self.bus.BusInv(self.cache_ID, addr)
                    self.cache_dict[key]["addr"] = addr
                    self.cache_dict[key]["offset"] = offset
                    #self.cache_dict[key]["data"] = data
                    self.cache_dict[key]["state"] = "M"
                lru_place, fill_place = self.lru_mechanism(hit, key, index)
        #state = "I"
        if (hit == False and
                len(self.line_queue[int(index, 2)]) != self.way):
            hit_place = None
            # Create a random line slot number
            lru_place, fill_place = self.lru_mechanism(hit, hit_place, index)
            pass_data = self.bus.BusRdX(self.cache_ID, addr)
            self.cache_dict[fill_place]["addr"] = addr
            self.cache_dict[fill_place]["tag"] = tag
            self.cache_dict[fill_place]["index"] = index
            self.cache_dict[fill_place]["offset"] = offset
            #self.cache_dict[fill_place]["data"] = data
            self.cache_dict[fill_place]["state"] = "M"
        elif (hit == False and
                len(self.line_queue[int(index, 2)]) == self.way):
            hit_place = None
            lru_place, fill_place = self.lru_mechanism(hit, hit_place, index)
        # evict S
            if self.cache_dict[lru_place]["state"] == "S":
                self.cache_dict[lru_place]["addr"] = addr
                self.cache_dict[lru_place]["tag"] = tag
                self.cache_dict[lru_place]["index"] = index
                self.cache_dict[lru_place]["offset"] = offset
                #self.cache_dict[lru_place]["data"] = data
                self.cache_dict[lru_place]["state"] = "M"
        # evict M
            elif self.cache_dict[lru_place]["state"] == "M":
                mem = True
                #mem_data = self.cache_dict[lru_place]["data"]
                mem_addr = self.cache_dict[lru_place]["addr"]
                self.cache_dict[lru_place]["addr"] = addr
                self.cache_dict[lru_place]["tag"] = tag
                self.cache_dict[lru_place]["index"] = index
                self.cache_dict[lru_place]["offset"] = offset
                #self.cache_dict[lru_place]["data"] = data
                self.cache_dict[lru_place]["state"] = "M"
        return hit, mem, mem_data, mem_addr

    def read(self, addr):
        hit = False
        mem = False
        mem_data = None
        pass_data = None
        mem_addr = None
        tag, index, offset = self.parse_address(addr)
        for key, val in self.cache_dict.items():
            if (tag == val["tag"] and
                    index == val["index"] and
                    self.cache_dict[key]["state"] != "I"):
                hit = True
        #state = "M"
                if self.cache_dict[key]["state"] == "M":
                    self.cache_dict[key]["addr"] = addr
                    self.cache_dict[key]["offset"] = offset
        # state = "S"
                else:
                    self.cache_dict[key]["addr"] = addr
                    self.cache_dict[key]["offset"] = offset
                lru_place, fill_place = self.lru_mechanism(hit, key, index)
        # state = "I"
        if (hit == False and
                len(self.line_queue[int(index, 2)]) != self.way):
            hit_place = None
            # Create a random line slot number
            lru_place, fill_place = self.lru_mechanism(hit, hit_place, index)
            pass_data, mem, mem_addr = self.bus.BusRd(self.cache_ID, addr)
            self.cache_dict[fill_place]["addr"] = addr
            self.cache_dict[fill_place]["tag"] = tag
            self.cache_dict[fill_place]["index"] = index
            self.cache_dict[fill_place]["offset"] = offset
            #self.cache_dict[fill_place]["data"] = pass_data
            self.cache_dict[fill_place]["state"] = "S"
            mem_data = pass_data
        elif (hit == False and
                len(self.line_queue[int(index, 2)]) == self.way):
            hit_place = None
            lru_place, fill_place = self.lru_mechanism(hit, hit_place, index)
        # evict S
            if self.cache_dict[lru_place]["state"] == "S":
                pass_data, mem, mem_addr = self.bus.BusRd(self.cache_ID, addr)
                self.cache_dict[lru_place]["addr"] = addr
                self.cache_dict[lru_place]["tag"] = tag
                self.cache_dict[lru_place]["index"] = index
                self.cache_dict[lru_place]["offset"] = offset
                #self.cache_dict[lru_place]["data"] = pass_data
        # evict M
            elif self.cache_dict[lru_place]["state"] == "M":
                pass_data, mem, mem_addr = self.bus.BusRd(self.cache_ID, addr)
                mem = True
                #mem_data = self.cache_dict[lru_place]["data"]
                mem_addr = self.cache_dict[lru_place]["addr"]
                self.cache_dict[lru_place]["addr"] = addr
                self.cache_dict[lru_place]["tag"] = tag
                self.cache_dict[lru_place]["index"] = index
                self.cache_dict[lru_place]["offset"] = offset
                #self.cache_dict[lru_place]["data"] = pass_data
                self.cache_dict[lru_place]["state"] = "S"
        return hit, mem, mem_data, mem_addr

    def handle_BusInv(self, addr):
        tag, index, offset = self.parse_address(addr)
        valid = False
        BusReply = None
        for key, val in self.cache_dict.items():
            if (tag == val["tag"] and
                    index == val["index"] and
                    self.cache_dict[key]["state"] != "I"):
                self.cache_dict[key]["state"] = "I"
                valid = True
                #BusReply = self.cache_dict[key]["data"]
                self.line_queue[int(index, 2)].remove(key)
        return valid, BusReply

    def handle_BusRd(self, addr):
        tag, index, offset = self.parse_address(addr)
        valid = False
        BusReply = None
        mem = False
        mem_addr = None
        for key, val in self.cache_dict.items():
            if (tag == val["tag"] and
                    index == val["index"] and
                    self.cache_dict[key]["state"] != "I"):
                #hit = True
                #state = "S"
                if self.cache_dict[key]["state"] == "S":
                    valid = True
                    #BusReply = self.cache_dict[key]["data"]
                # state = "M"
                else:
                    valid = True
                    self.cache_dict[key]["state"] = "S"
                    #BusReply = self.cache_dict[key]["data"]
                    # mem snarf
                    mem = True
                    mem_addr = addr
                    self.cache_dict[key]["addr"] = addr
                    self.cache_dict[key]["offset"] = offset
                #self.line_queue.remove(key)
                #self.line_queue.append(key)
        return valid, BusReply, mem, mem_addr

    def handle_BusRdX(self, addr):
        tag, index, offset = self.parse_address(addr)
        valid = False
        BusReply = None
        for key, val in self.cache_dict.items():
            if (tag == val["tag"] and
                    index == val["index"] and
                    self.cache_dict[key]["state"] != "I"):
                # state = "S" and "M"
                valid = True
                #BusReply = self.cache_dict[key]["data"]
                self.cache_dict[key]["state"] = "I"
                self.line_queue[int(index, 2)].remove(key)
        return valid, BusReply

    def lru_mechanism(self, hit, hit_place, index):
        lru_place = None
        fill_place = None
        if hit:
            self.line_queue[int(index, 2)].remove(hit_place)
            self.line_queue[int(index, 2)].append(hit_place)
        if hit == False:
            #Set is full
            if len(self.line_queue[int(index, 2)]) == self.way:
                lru_place = self.line_queue[int(index, 2)][0]
                self.line_queue[int(index, 2)].append(self.line_queue[int(index, 2)][0])
                self.line_queue[int(index, 2)].pop(0)
            #Set is still empty
            else:
                fill_place = str(random.randint((int(index, 2) * self.way), (int(index, 2) * self.way) + self.way - 1))
                while (fill_place in self.line_queue[int(index, 2)]):
                    fill_place = str(random.randint((int(index, 2) * self.way), (int(index, 2) * self.way) + self.way - 1))
                self.line_queue[int(index, 2)].append(fill_place)
        return lru_place, fill_place

    def parse_address(self, addr):
        addr_bin = self.decimal2binary(addr, self.addr_bits)
        # Setup tag, index, offset
        if self.way == self.cache_num_line:
            index_bit = 0
        else:
            index_bit = int(math.log2(self.cache_num_line / self.way))
        offset_bit = int(math.log2(self.cache_line_size))
        tag_bit = self.addr_bits - index_bit - offset_bit

        tag = addr_bin[0:tag_bit]
        if self.way == self.cache_num_line:
            index = "0"
        else:
            index = addr_bin[tag_bit:(self.addr_bits - offset_bit)]
        offset = addr_bin[(self.addr_bits - offset_bit):]
        return tag, index, offset

def json_dump(filepath, dict):

    with open(filepath, 'w', encoding='utf-8') as file_obj:
        json.dump(dict, file_obj, ensure_ascii=False, indent=2)



def main():
    processors = 4
    shared_bus = bus()
    caches = []
    #for cache_id in range(processors):
    #   cache = nway_cache(cache_id)
    #   caches.append(cache)
    c = direct_cache(0)
    b = direct_cache(1)
    caches.append(c)
    caches.append(b)
    #print(c.operation("st", 66, 45))
    print(c.write(66, 45))
    #print(c.write(194, 75))
    print(b.read(66))
    #print(c.operation("st", 332, 40))
    #print(c.operation("st", 167, 57))
    print(c.write(66, 67))
    print(c.write(194, 50))
    c.print_cache()
    b.print_cache()
    #print()


    dump_dict = {}
    #for i in cache_list:
    dump_dict.update(c.return_cache_dict())
    json_dump("cache.json", dump_dict)

if __name__ == "__main__":
	main()