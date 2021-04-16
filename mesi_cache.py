# Cache Class for mesi.py
import math
import random

class cache():

    def __init__(self, ID, size, line_size, mem_size, file, LSR, PC):
        self.cache_ID = ID
        self.cache_size = size # Bytes
        self.cache_line_size = line_size #Bytes
        self.cache_dict = {}
        self.addr_bits = int(math.log2(mem_size))
        self.cache_num_line = int(size/line_size)
        # For LSR
        self.line_queue = LSR
        # PC
        self.PC = PC

        if file == None:
            for i in range(self.cache_num_line):
                self.cache_dict[str(i)] = {"addr": None,
                                           "tag": None,
                                           "index": None,
                                           "offset": None,
                                           "protocol": "I"}
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

    def __init__(self, ID, size = 128, line_size = 8, mem_size = 512, file = None, LSR = [], PC = 0):
        super().__init__(ID, size, line_size, mem_size, file, LSR, PC)

    def cache_operation(self, inst, addr):
        hit = False
        bus_info = None
        addr_bin = self.decimal2binary(addr, self.addr_bits)

        # Setup tag, index, offset
        index_bit  = int(math.log2(self.cache_num_line))
        offset_bit = int(math.log2(self.cache_line_size))
        tag_bit    = self.addr_bits - index_bit - offset_bit

        tag    = addr_bin[0:tag_bit]
        index  = addr_bin[tag_bit:(self.addr_bits - offset_bit)]
        offset = addr_bin[(self.addr_bits - offset_bit):]

        # Inst = Store
        if inst == "st":
            # Hit
            for key, val in self.cache_dict.items():
                if index == val["index"] and tag == val["tag"] and val["protocol"] != "I":
                    hit = True
                    if   val["protocol"] == "M":
                        val["protocol"] = "M"
                    elif val["protocol"] == "E":
                        val["protocol"] = "M"
                    elif val["protocol"] == "S":
                        val["protocol"] = "M"
                        bus_info = "BusInv"
            # Miss
            if hit == False:
                self.cache_dict[str(int(index,2))]["addr"]     = addr
                self.cache_dict[str(int(index,2))]["tag"]      = tag
                self.cache_dict[str(int(index,2))]["index"]    = index
                self.cache_dict[str(int(index,2))]["offset"]   = offset
                self.cache_dict[str(int(index,2))]["protocol"] = "M"
                bus_info = "BusRdX"
        
        # Inst = Load
        if inst == "ld":
            # Hit
            for key, val in self.cache_dict.items():
                if index == val["index"] and tag == val["tag"] and val["protocol"] != "I":
                    hit = True
                    if   val["protocol"] == "M":
                        val["protocol"] = "M"
                    elif val["protocol"] == "E":
                        val["protocol"] = "E"
                    elif val["protocol"] == "S":
                        val["protocol"] = "S"
            # Miss
            if hit == False:
                self.cache_dict[str(int(index,2))]["addr"]     = addr
                self.cache_dict[str(int(index,2))]["tag"]      = tag
                self.cache_dict[str(int(index,2))]["index"]    = index
                self.cache_dict[str(int(index,2))]["offset"]   = offset
                self.cache_dict[str(int(index,2))]["protocol"] = "E" # fix it
                bus_info = "BusRd"

        return {"hit": hit, "bus_info": bus_info, "dict_key": str(int(index,2))}

    def bus_operation(self, bus_info, addr):
        addr_bin  = self.decimal2binary(addr, self.addr_bits)
        hit       = False
        bus_reply = False
        mem_wb    = False

        # Setup tag, index, offset
        index_bit  = int(math.log2(self.cache_num_line))
        offset_bit = int(math.log2(self.cache_line_size))
        tag_bit    = self.addr_bits - index_bit - offset_bit

        tag    = addr_bin[0:tag_bit]
        index  = addr_bin[tag_bit:(self.addr_bits - offset_bit)]
        offset = addr_bin[(self.addr_bits - offset_bit):]

        for key, val in self.cache_dict.items():
            if index == val["index"] and tag == val["tag"] and val["protocol"] != "I":
                if   val["protocol"] == "M":
                    if bus_info == "BusRd":
                        val["protocol"] = "S"
                        bus_reply       = True
                        mem_wb          = True
                    if bus_info == "BusRdX":
                        val["protocol"] = "I"
                        bus_reply       = True
                        mem_wb          = True
                    if bus_info == "BusInv":
                        val["protocol"] = "I"
                        mem_wb          = True
                    if bus_info == "BusReply":
                        pass
                elif val["protocol"] == "E":
                    if bus_info == "BusRd":
                        val["protocol"] = "S"
                        bus_reply       = True
                    if bus_info == "BusRdX":
                        val["protocol"] = "I"
                        bus_reply       = True
                    if bus_info == "BusInv":
                        val["protocol"] = "I"
                    if bus_info == "BusReply":
                        pass
                elif val["protocol"] == "S":
                    if bus_info == "BusRd":
                        bus_reply = True
                    if bus_info == "BusRdX":
                        val["protocol"] = "I"
                        bus_reply       = True
                    if bus_info == "BusInv":
                        val["protocol"] = "I"
                    if bus_info == "BusReply":
                        pass

        return {"hit": hit, "bus_reply": bus_reply, "mem_wb": mem_wb}

# Fully Associative
class fully_cache(cache):

    def __init__(self, ID, size = 128, line_size = 8, mem_size = 512, file = None, LSR = [], PC = 0):
        super().__init__(ID, size, line_size, mem_size, file, LSR, PC)

    def cache_operation(self, inst, addr):
        e2s_key  = None
        hit      = False
        bus_info = None
        addr_bin = self.decimal2binary(addr, self.addr_bits)

        # Setup tag, index, offset
        index_bit  = 0
        offset_bit = int(math.log2(self.cache_line_size))
        tag_bit    = self.addr_bits - index_bit - offset_bit

        tag    = addr_bin[0:tag_bit]
        index  = None
        offset = addr_bin[(self.addr_bits - offset_bit):]

        # Inst = Store
        if inst == "st":
            # Hit
            for key, val in self.cache_dict.items():
                if tag == val["tag"] and val["protocol"] != "I":
                    hit = True
                    self.line_queue.remove(key)
                    self.line_queue.append(key)
                    if   val["protocol"] == "M":
                        val["protocol"] = "M"
                    elif val["protocol"] == "E":
                        val["protocol"] = "M"
                    elif val["protocol"] == "S":
                        val["protocol"] = "M"  
                        bus_info = "BusInv"
            # Miss
            if hit == False:
                # Queue is full
                if len(self.line_queue) == self.cache_num_line:
                    self.cache_dict[self.line_queue[0]]["addr"]     = addr
                    self.cache_dict[self.line_queue[0]]["tag"]      = tag
                    self.cache_dict[self.line_queue[0]]["index"]    = index
                    self.cache_dict[self.line_queue[0]]["offset"]   = offset
                    self.cache_dict[self.line_queue[0]]["protocol"] = "M"
                    self.line_queue.append(self.line_queue[0])
                    self.line_queue.pop(0)
                    bus_info = "BusRdX"

                # Queue is not full yet
                else: 
                    # Create a random line slot number
                    num = str(random.randint(0, self.cache_num_line - 1))
                    while (num in self.line_queue):
                        num = str(random.randint(0, self.cache_num_line - 1))

                    self.cache_dict[num]["addr"]     = addr
                    self.cache_dict[num]["tag"]      = tag
                    self.cache_dict[num]["index"]    = index
                    self.cache_dict[num]["offset"]   = offset
                    self.cache_dict[num]["protocol"] = "M"
                    self.line_queue.append(num)
                    bus_info = "BusRdX"
        
        # Inst = Load
        if inst == "ld":
            # Hit
            for key, val in self.cache_dict.items():
                if tag == val["tag"] and val["protocol"] != "I":
                    hit = True
                    self.line_queue.remove(key)
                    self.line_queue.append(key)
                    if   val["protocol"] == "M":
                        val["protocol"] = "M"
                    elif val["protocol"] == "E":
                        val["protocol"] = "E"
                    elif val["protocol"] == "S":
                        val["protocol"] = "S"
            # Miss
            if hit == False:
                # Queue is full
                if len(self.line_queue) == self.cache_num_line:
                    self.cache_dict[self.line_queue[0]]["addr"]     = addr
                    self.cache_dict[self.line_queue[0]]["tag"]      = tag
                    self.cache_dict[self.line_queue[0]]["index"]    = index
                    self.cache_dict[self.line_queue[0]]["offset"]   = offset
                    self.cache_dict[self.line_queue[0]]["protocol"] = "E" # fix it
                    self.line_queue.append(self.line_queue[0])
                    self.line_queue.pop(0)
                    bus_info = "BusRd"
                    e2s_key  = self.line_queue[0]

                # Queue is not full yet
                else: 
                    # Create a random line slot number
                    num = str(random.randint(0, self.cache_num_line - 1))
                    while (num in self.line_queue):
                        num = str(random.randint(0, self.cache_num_line - 1))

                    self.cache_dict[num]["addr"]     = addr
                    self.cache_dict[num]["tag"]      = tag
                    self.cache_dict[num]["index"]    = index
                    self.cache_dict[num]["offset"]   = offset
                    self.cache_dict[num]["protocol"] = "E" # fix it
                    self.line_queue.append(num)
                    bus_info = "BusRd"
                    e2s_key  = num

        return {"hit": hit, "bus_info": bus_info, "dict_key": e2s_key}
    
    def bus_operation(self, bus_info, addr):
        addr_bin = self.decimal2binary(addr, self.addr_bits)
        hit       = False
        bus_reply = False
        mem_wb    = False

        # Setup tag, index, offset
        index_bit  = 0
        offset_bit = int(math.log2(self.cache_line_size))
        tag_bit    = self.addr_bits - index_bit - offset_bit

        tag    = addr_bin[0:tag_bit]
        index  = None
        offset = addr_bin[(self.addr_bits - offset_bit):]

        for key, val in self.cache_dict.items():
            if index == val["index"] and tag == val["tag"] and val["protocol"] != "I":
                if   val["protocol"] == "M":
                    if bus_info == "BusRd":
                        val["protocol"] = "S"
                        bus_reply       = True
                        mem_wb          = True
                    if bus_info == "BusRdX":
                        val["protocol"] = "I"
                        bus_reply       = True
                        mem_wb          = True
                    if bus_info == "BusInv":
                        val["protocol"] = "I"
                        mem_wb          = True
                    if bus_info == "BusReply":
                        pass
                elif val["protocol"] == "E":
                    if bus_info == "BusRd":
                        val["protocol"] = "S"
                        bus_reply       = True
                    if bus_info == "BusRdX":
                        val["protocol"] = "I"
                        bus_reply       = True
                    if bus_info == "BusInv":
                        val["protocol"] = "I"
                    if bus_info == "BusReply":
                        pass
                elif val["protocol"] == "S":
                    if bus_info == "BusRd":
                        bus_reply = True
                    if bus_info == "BusRdX":
                        val["protocol"] = "I"
                        bus_reply       = True
                    if bus_info == "BusInv":
                        val["protocol"] = "I"
                    if bus_info == "BusReply":
                        pass

        return {"hit": hit, "bus_reply": bus_reply, "mem_wb": mem_wb}

# N-way Associative
class nway_cache(cache):

    def __init__(self, ID, size = 128, line_size = 8, mem_size = 512, way = 2, file = None, LSR = [], PC = 0):
        super().__init__(ID, size, line_size, mem_size, file, LSR, PC)
        self.way = way

        if len(LSR) == 0:
            for i in range(int(self.cache_num_line/self.way)):
                list_temp = []
                self.line_queue.append(list_temp)

    def cache_operation(self, inst, addr):
        e2s_key  = None
        hit      = False
        bus_info = None
        addr_bin = self.decimal2binary(addr, self.addr_bits)

        # Setup tag, index, offset
        if self.way == self.cache_num_line:
            index_bit = 0
        else:
            index_bit  = int(math.log2(self.cache_num_line/self.way))
        offset_bit = int(math.log2(self.cache_line_size))
        tag_bit    = self.addr_bits - index_bit - offset_bit

        tag    = addr_bin[0:tag_bit]
        if self.way == self.cache_num_line:
            index = "0"
        else:
            index  = addr_bin[tag_bit:(self.addr_bits - offset_bit)]
        offset = addr_bin[(self.addr_bits - offset_bit):]

        # Inst = Store
        if inst == "st":
            # Hit
            for key, val in self.cache_dict.items():
                if index == val["index"] and tag == val["tag"] and val["protocol"] != "I":
                    hit = True
                    self.line_queue[int(index, 2)].remove(key)
                    self.line_queue[int(index, 2)].append(key)
                    if   val["protocol"] == "M":
                        val["protocol"] = "M"
                    elif val["protocol"] == "E":
                        val["protocol"] = "M"
                    elif val["protocol"] == "S":
                        val["protocol"] = "M"
                        bus_info = "BusInv"
            # Miss
            if hit == False:
                # Queue is full
                if len(self.line_queue[int(index, 2)]) == self.way:
                    self.cache_dict[self.line_queue[int(index, 2)][0]]["addr"]     = addr
                    self.cache_dict[self.line_queue[int(index, 2)][0]]["tag"]      = tag
                    self.cache_dict[self.line_queue[int(index, 2)][0]]["index"]    = index
                    self.cache_dict[self.line_queue[int(index, 2)][0]]["offset"]   = offset
                    self.cache_dict[self.line_queue[int(index, 2)][0]]["protocol"] = "M"
                    self.line_queue[int(index, 2)].append(self.line_queue[int(index, 2)][0])
                    self.line_queue[int(index, 2)].pop(0)
                    bus_info = "BusRdX"

                # Queue is not full yet
                else: 
                    # Create a random line slot number
                    num = str(random.randint((int(index, 2) * self.way), (int(index, 2) * self.way) + self.way - 1))
                    while (num in self.line_queue[int(index, 2)]):
                        num = str(random.randint((int(index, 2) * self.way), (int(index, 2) * self.way) + self.way - 1))

                    self.cache_dict[num]["addr"]     = addr
                    self.cache_dict[num]["tag"]      = tag
                    self.cache_dict[num]["index"]    = index
                    self.cache_dict[num]["offset"]   = offset
                    self.cache_dict[num]["protocol"] = "M"
                    self.line_queue[int(index, 2)].append(num)
                    bus_info = "BusRdX"

        # Inst = Load
        if inst == "ld":
            # Hit
            for key, val in self.cache_dict.items():
                if index == val["index"] and tag == val["tag"] and val["protocol"] != "I":
                    hit = True
                    self.line_queue[int(index, 2)].remove(key)
                    self.line_queue[int(index, 2)].append(key)
                    if   val["protocol"] == "M":
                        val["protocol"] = "M"
                    elif val["protocol"] == "E":
                        val["protocol"] = "E"
                    elif val["protocol"] == "S":
                        val["protocol"] = "S"
            # Miss
            if hit == False:
                # Queue is full
                if len(self.line_queue[int(index, 2)]) == self.way:
                    self.cache_dict[self.line_queue[int(index, 2)][0]]["addr"]     = addr
                    self.cache_dict[self.line_queue[int(index, 2)][0]]["tag"]      = tag
                    self.cache_dict[self.line_queue[int(index, 2)][0]]["index"]    = index
                    self.cache_dict[self.line_queue[int(index, 2)][0]]["offset"]   = offset
                    self.cache_dict[self.line_queue[int(index, 2)][0]]["protocol"] = "E" # fix it
                    self.line_queue[int(index, 2)].append(self.line_queue[int(index, 2)][0])
                    self.line_queue[int(index, 2)].pop(0)
                    bus_info = "BusRd"
                    e2s_key = self.line_queue[int(index, 2)][0]

                # Queue is not full yet
                else: 
                    # Create a random line slot number
                    num = str(random.randint((int(index, 2) * self.way), (int(index, 2) * self.way) + self.way - 1))
                    while (num in self.line_queue[int(index, 2)]):
                        num = str(random.randint((int(index, 2) * self.way), (int(index, 2) * self.way) + self.way - 1))

                    self.cache_dict[num]["addr"]     = addr
                    self.cache_dict[num]["tag"]      = tag
                    self.cache_dict[num]["index"]    = index
                    self.cache_dict[num]["offset"]   = offset
                    self.cache_dict[num]["protocol"] = "E" # fix it
                    self.line_queue[int(index, 2)].append(num)
                    bus_info = "BusRd"
                    e2s_key = num

        return {"hit": hit, "bus_info": bus_info, "dict_key": e2s_key}

    def bus_operation(self, bus_info, addr):
        addr_bin = self.decimal2binary(addr, self.addr_bits)
        hit       = False
        bus_reply = False
        mem_wb    = False

        # Setup tag, index, offset
        if self.way == self.cache_num_line:
            index_bit = 0
        else:
            index_bit  = int(math.log2(self.cache_num_line/self.way))
        offset_bit = int(math.log2(self.cache_line_size))
        tag_bit    = self.addr_bits - index_bit - offset_bit

        tag    = addr_bin[0:tag_bit]
        if self.way == self.cache_num_line:
            index = "0"
        else:
            index  = addr_bin[tag_bit:(self.addr_bits - offset_bit)]
        offset = addr_bin[(self.addr_bits - offset_bit):]

        for key, val in self.cache_dict.items():
            if index == val["index"] and tag == val["tag"] and val["protocol"] != "I":
                if   val["protocol"] == "M":
                    if bus_info == "BusRd":
                        val["protocol"] = "S"
                        bus_reply       = True
                        mem_wb          = True
                    if bus_info == "BusRdX":
                        val["protocol"] = "I"
                        bus_reply       = True
                        mem_wb          = True
                    if bus_info == "BusInv":
                        val["protocol"] = "I"
                        mem_wb          = True
                    if bus_info == "BusReply":
                        pass
                elif val["protocol"] == "E":
                    if bus_info == "BusRd":
                        val["protocol"] = "S"
                        bus_reply       = True
                    if bus_info == "BusRdX":
                        val["protocol"] = "I"
                        bus_reply       = True
                    if bus_info == "BusInv":
                        val["protocol"] = "I"
                    if bus_info == "BusReply":
                        pass
                elif val["protocol"] == "S":
                    if bus_info == "BusRd":
                        bus_reply = True
                    if bus_info == "BusRdX":
                        val["protocol"] = "I"
                        bus_reply       = True
                    if bus_info == "BusInv":
                        val["protocol"] = "I"
                    if bus_info == "BusReply":
                        pass

        return {"hit": hit, "bus_reply": bus_reply, "mem_wb": mem_wb}