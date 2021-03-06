# Cache Class for mesi.py
import math
import random

class cache():

    def __init__(self, ID, size = 128, line_size = 8, mem_size = 512, cache_mode = "direct", way = 2):
        self.cache_ID = ID
        self.cache_size = size # Bytes
        self.cache_line_size = line_size #Bytes
        self.cache_dict = {}
        self.addr_bits = int(math.log2(mem_size))
        self.cache_num_line = int(size/line_size)
        self.cache_mode = cache_mode
        # For N-way Associate
        if self.cache_mode == "way":
            self.way = way
        # For Fully Associate LSR
        if self.cache_mode == "full":
            self.line_queue = []
        # For N-way Associate LSR
        if self.cache_mode == "way":
            self.line_queue = []
            for i in range(int(self.cache_num_line/self.way)):
                list_temp = []
                self.line_queue.append(list_temp)

        for i in range(self.cache_num_line):
            self.cache_dict[i] = {"addr": None,
                                  "tag": None,
                                  "index": None,
                                  "offset": None,
                                  "protocol": "I"}

    # transfer decimal to binary and pad with zero
    def decimal2binary(self, num, bits):
        binary = bin(num)[2:].zfill(bits)
        return binary

    def operation(self, inst, addr):
        hit = False
        addr_bin = self.decimal2binary(addr, self.addr_bits)

        # Direct-map
        if self.cache_mode == "direct":
            # Setup tag, index, offset
            index_bit  = int(math.log2(self.cache_num_line))
            offset_bit = int(math.log2(self.cache_line_size))
            tag_bit    = self.addr_bits - index_bit - offset_bit

            tag    = addr_bin[0:tag_bit]
            index  = addr_bin[tag_bit:(self.addr_bits - offset_bit)]
            offset = addr_bin[(self.addr_bits - offset_bit):]

            # Inst = Store or Load
            if inst == "st" or inst == "ld":
                # Hit
                for key, val in self.cache_dict.items():
                    if index == val["index"] and tag == val["tag"]:
                        hit = True
                # Miss
                if hit == False:
                    self.cache_dict[int(index,2)]["addr"]   = addr
                    self.cache_dict[int(index,2)]["tag"]    = tag
                    self.cache_dict[int(index,2)]["index"]  = index
                    self.cache_dict[int(index,2)]["offset"] = offset


        # N-way Associate
        if self.cache_mode == "way":
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


        # Fully Associate
        if self.cache_mode == "full":
            # Setup tag, index, offset
            index_bit  = 0
            offset_bit = int(math.log2(self.cache_line_size))
            tag_bit    = self.addr_bits - index_bit - offset_bit

            tag    = addr_bin[0:tag_bit]
            index  = None
            offset = addr_bin[(self.addr_bits - offset_bit):]

            # Inst = Store
            if inst == "st" or inst == "ld":
                # Hit
                for key, val in self.cache_dict.items():
                    if tag == val["tag"]:
                        hit = True
                        self.line_queue.remove(key)
                        self.line_queue.append(key)
                # Miss
                if hit == False:
                    # Queue is full
                    if len(self.line_queue) == self.cache_num_line:
                        self.cache_dict[self.line_queue[0]]["addr"]   = addr
                        self.cache_dict[self.line_queue[0]]["tag"]    = tag
                        self.cache_dict[self.line_queue[0]]["index"]  = index
                        self.cache_dict[self.line_queue[0]]["offset"] = offset
                        self.line_queue.append(self.line_queue[0])
                        self.line_queue.pop(0)

                    # Queue is not full yet
                    else: 
                        # Create a random line slot number
                        num = random.randint(0, self.cache_num_line - 1)
                        while (num in self.line_queue):
                            num = random.randint(0, self.cache_num_line - 1)

                        self.cache_dict[num]["addr"]   = addr
                        self.cache_dict[num]["tag"]    = tag
                        self.cache_dict[num]["index"]  = index
                        self.cache_dict[num]["offset"] = offset
                        self.line_queue.append(num)

        return hit

    def print_cache(self):
        for key, val in self.cache_dict.items():
            print(f"line[{key}] = {val}")

