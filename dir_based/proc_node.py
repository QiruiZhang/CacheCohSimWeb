# -*- coding: utf-8 -*-
import math

# cache class from modified from Danny's implementation
class cache():
    def __init__(self, ID, size, line_size, mem_size, file, LSR):
        self.cache_ID = ID
        self.cache_size = size # Bytes
        self.cache_line_size = line_size #Bytes
        self.cache_dict = {}
        self.addr_bits = int(math.log2(mem_size))
        self.cache_num_line = int(size/line_size)
         # For LSR
        self.line_queue = LSR

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
        return {self.cache_ID: {"cache": self.cache_dict, "LSR": self.line_queue}}

# Processor node class inherited from cache: core + cache + cache-ctrl + msg-queues
class proc_node(cache):
    # Object initialization
    def __init__(self, ID, inst = [], protocol = 'MSI', size = 128, line_size = 8, mem_size = 512, cache_file = None, LSR = [], print_flag = True):
        super().__init__(ID, size, line_size, mem_size, cache_file, LSR) # Inheritance
        
        self.print_flag = print_flag
        
        self.insts = inst # Input instructions from user
        self.protocol = protocol # Protocol type: MSI, MESI or MOSI
        self.PC = 0 # PC is only accumulated when processor is not stalled
                
        self.CRHR_inst = ["nop", 0]
        self.CRHR = False # Coherence Request Handling Register
        self.inv_ack_cnt = 0
        self.inv_ack = 0
        
        self.msgq_fwd = [] # Input msg queue/channel for forwarded msgs
        self.msgq_inv = [] # Input msg queue/channel for invalidations
        self.msgq_other = [] # Input msg queue/channel for other msgs
    
        self.msg_out = {
            "type": "None",
            "ack": 0, # Used only when type is Data-FD (Data from Directory)
            "addr": 0,
            "src": "node_" + str(ID),
            "dst": "dir"
        } # Output msg updated per cycle for addr-of-attention
    
        self.msg_out_ch2 = {
            "type": "None",
            "ack": 0, # Used only when type is Data-FD (Data from Directory)
            "addr": 0,
            "src": "node_" + str(ID),
            "dst": "dir"
        } # Output msg updated per cycle for addr-out-of-attention

        ''' Message Types
            Dir->node and node<->node message types:
                Fwd-GetS
                Fwd-GetM
                Inv
                Put-Ack
                Data-FD (Data from Dir)
                Data-FO (Data from Owner)
                Inv-Ack
                
            node->Dir message types:
                GetS
                GetM
                PutS
                PutM
                Data-TRD (Data to Dir and Req)
                Data-TR (Data to Req)
        '''
    
    # Input messages into the queues, used by simulator main program
    def input_msg(self, msg):
        if msg['type'] == 'Fwd-GetS' or msg['type'] == 'Fwd-GetM':
            self.msgq_fwd.append(msg)
        elif msg['type'] == 'Inv':
            self.msgq_inv.append(msg)
        else:
            self.msgq_other.append(msg)
    
    # Get message output of the current cycle
    def get_msg_out(self):
        return [self.msg_out, self.msg_out_ch2]
    
    # Update the processor node state by one cycle
    def proc_run(self):
        if self.protocol == 'MSI':
            self.cache_ctrl_msi()
        elif self.protocol == 'MESI':
            self.cache_ctrl_mesi()
        elif self.protocol == 'MOSI':
            self.cache_ctrl_mosi()
        else:
            pass
    
    # MSI cache coherence protocol controller
    def cache_ctrl_msi(self):
      # First handle processor-side instructions
        if (not self.CRHR):
            self.CRHR_inst = self.insts[self.PC]
            self.PC += 1
        op = self.CRHR_inst[0]
        addr = self.CRHR_inst[1]
        
        # Setup tag, index, offset
        addr_bin = self.decimal2binary(addr, self.addr_bits)
        index_bits  = int(math.log2(self.cache_num_line))
        offset_bits = int(math.log2(self.cache_line_size))
        tag_bits    = self.addr_bits - index_bits - offset_bits
        tag    = addr_bin[0:tag_bits]
        index  = addr_bin[tag_bits:(self.addr_bits - offset_bits)]
        offset = addr_bin[(self.addr_bits - offset_bits):]
        index_dec = int(index, 2)
        cache_line = self.cache_dict[str(index_dec)]
        
        # default empty output message
        self.msg_out = {
            "type": "None",
            "ack": 0,
            "addr": 0,
            "src": "node_" + str(self.cache_ID),
            "dst": "dir"
        }

        # Finite State Machine from ch8 of 'A Primer on Memory Consistency and Cache Coherence'
        if op != "nop": # only attend to the instruction when it is not no-op
          # State: I
            if cache_line["protocol"] == "I":
                if op == "ld": # Send GetS to Dir/IS_D
                    # update output msg
                    self.msg_out = {
                        "type": "GetS",
                        "ack": 0,
                        "addr": addr,
                        "src": "node_" + str(self.cache_ID),
                        "dst": "dir"
                        }
                    # update cache line
                    self.cache_dict[str(index_dec)]["protocol"] = "IS_D"
                    self.cache_dict[str(index_dec)]["addr"] = addr
                    self.cache_dict[str(index_dec)]["tag"] = tag
                    self.cache_dict[str(index_dec)]["index"] = index
                    self.cache_dict[str(index_dec)]["offset"] = offset
                    if (self.print_flag): 
                        print("State Transition: I->IS_D @ $-line-" + str(index_dec) + " with addr " + str(addr) + "!")
                    # update CRHR
                    self.CRHR = True
                elif op == "st": # Send GetM to Dir/IM_AD
                    # update output msg
                    self.msg_out = {
                        "type": "GetM",
                        "ack": 0,
                        "addr": addr,
                        "src": "node_" + str(self.cache_ID),
                        "dst": "dir"
                    }    
                    # update cache line
                    self.cache_dict[str(index_dec)]["protocol"] = "IM_AD"
                    self.cache_dict[str(index_dec)]["addr"] = addr
                    self.cache_dict[str(index_dec)]["tag"] = tag
                    self.cache_dict[str(index_dec)]["index"] = index
                    self.cache_dict[str(index_dec)]["offset"] = offset
                    if (self.print_flag): 
                        print("State Transition: I->IM_AD @ $-line-" + str(index_dec) + " with addr " + str(addr) + "!")
                    # update CRHR
                    self.CRHR = True
          # State: IS_D
            elif cache_line["protocol"] == "IS_D":
                if (len(self.msgq_other) != 0) and (self.msgq_other[0]["type"] == "Data-FD" or self.msgq_other[0]["type"] == "Data-FO") and (self.msgq_other[0]["addr"] == addr):
                    # Pop msg queue
                    self.msgq_other.pop(0)
                    # update cache line
                    self.cache_dict[str(index_dec)]["protocol"] = "S"
                    if (self.print_flag):
                        print("State Transition: IS_D->S @ $-line-" + str(index_dec) + " with addr " + str(addr) + "!")
                    # update CRHR
                    self.CRHR = False
          # State: IM_AD
            elif cache_line["protocol"] == "IM_AD":
                if (len(self.msgq_other) != 0) and (self.msgq_other[0]["addr"] == addr):
                    if(self.msgq_other[0]["type"] == "Inv-Ack"):
                        # Pop msg queue
                        self.msgq_other.pop(0)
                        # update CRHR
                        self.inv_ack_cnt += 1
                    elif (self.msgq_other[0]["type"] == "Data-FO"):
                        # Pop msg queue
                        self.msgq_other.pop(0)
                        # update cache line
                        self.cache_dict[str(index_dec)]["protocol"] = "M"
                        if (self.print_flag):
                            print("State Transition: IM_AD->M @ $-line-" + str(index_dec) + " with addr " + str(addr) + "!")
                        # update CRHR
                        self.CRHR = False
                    elif (self.msgq_other[0]["type"] == "Data-FD" and self.msgq_other[0]["ack"] == 0):
                        # Pop msg queue
                        self.msgq_other.pop(0)
                        # update cache line
                        self.cache_dict[str(index_dec)]["protocol"] = "M"
                        if (self.print_flag):
                            print("State Transition: IM_AD->M @ $-line-" + str(index_dec) + " with addr " + str(addr) + "!") 
                        # update CRHR
                        self.CRHR = False
                    elif (self.msgq_other[0]["type"] == "Data-FD" and self.msgq_other[0]["ack"] > 0):
                        # update CRHR
                        self.inv_ack = self.msgq_other[0]["ack"]
                        # Pop msg queue
                        self.msgq_other.pop(0)
                        # update cache line
                        self.cache_dict[str(index_dec)]["protocol"] = "IM_A"
                        if (self.print_flag):
                            print("State Transition: IM_AD->IM_A @ $-line-" + str(index_dec) + " with addr " + str(addr) + "!")    
          # State: IM_A
            elif cache_line["protocol"] == "IM_A":
                if (self.inv_ack == self.inv_ack_cnt): # Already received enough ack during IM_AD
                    # update CRHR
                    self.inv_ack = 0
                    self.inv_ack_cnt = 0
                    self.CRHR = False
                    # update cache line
                    self.cache_dict[str(index_dec)]["protocol"] = "M"
                    if (self.print_flag):
                        print("State Transition: IM_A->M @ $-line-" + str(index_dec) + " with addr " + str(addr) + "!")
                elif (len(self.msgq_other) != 0) and (self.msgq_other[0]["type"] == "Inv-Ack") and (self.msgq_other[0]["addr"] == addr):
                    # Pop msg queue
                    self.msgq_other.pop(0)
                    # update CRHR
                    self.inv_ack_cnt += 1
                    if (self.inv_ack == self.inv_ack_cnt): # if Last Ack
                        # update CRHR
                        self.inv_ack = 0
                        self.inv_act_cnt = 0
                        self.CRHR = False
                        # update cache line
                        self.cache_dict[str(index_dec)]["protocol"] = "M"
                        if (self.print_flag):
                            print("State Transition: IM_A->M @ $-line-" + str(index_dec) + " with addr " + str(addr) + "!")
          # State: S
            elif cache_line["protocol"] == "S":
                if op == "st":
                    # update output msg
                    self.msg_out = {
                        "type": "GetM",
                        "ack": 0,
                        "addr": addr,
                        "src": "node_" + str(self.cache_ID),
                        "dst": "dir"
                    }
                    # update cache line
                    self.cache_dict[str(index_dec)]["protocol"] = "SM_AD"
                    self.cache_dict[str(index_dec)]["addr"] = addr
                    self.cache_dict[str(index_dec)]["tag"] = tag
                    self.cache_dict[str(index_dec)]["index"] = index
                    self.cache_dict[str(index_dec)]["offset"] = offset
                    if (self.print_flag): 
                        print("State Transition: S->SM_AD @ $-line-" + str(index_dec) + " with addr " + str(addr) + "!")
                    # update CRHR
                    self.CRHR = True
                elif op == "ev":
                    # update output msg
                    self.msg_out = {
                        "type": "PutS",
                        "ack": 0,
                        "addr": addr,
                        "src": "node_" + str(self.cache_ID),
                        "dst": "dir"
                    }
                    # update cache line
                    self.cache_dict[str(index_dec)]["protocol"] = "SI_A"
                    if (self.print_flag): 
                        print("State Transition: S->SI_A @ $-line-" + str(index_dec) + " with addr " + str(addr) + "!")
                    # update CRHR
                    self.CRHR = True
                elif (len(self.msgq_inv) != 0) and (self.msgq_inv[0]["addr"] == addr):
                    # update output msg
                    self.msg_out = {
                        "type": "Inv-Ack",
                        "ack": 0,
                        "addr": addr,
                        "src": "node_" + str(self.cache_ID),
                        "dst": self.msgq_inv[0]["src"]
                    }
                    # Pop msg queue
                    self.msgq_inv.pop(0)
                    # update cache line
                    self.cache_dict[str(index_dec)]["protocol"] = "I"
                    self.cache_dict[str(index_dec)]["addr"] = None
                    self.cache_dict[str(index_dec)]["tag"] = None
                    self.cache_dict[str(index_dec)]["index"] = None
                    self.cache_dict[str(index_dec)]["offset"] = None
                    if (self.print_flag): 
                        print("State Transition: S->I @ $-line-" + str(index_dec) + " with addr " + str(addr) + "!")
          # State: SM_AD
            elif cache_line["protocol"] == "SM_AD":
                if (len(self.msgq_inv) != 0) and (self.msgq_inv[0]["addr"] == addr): # Check Inv first
                    # update output msg
                    self.msg_out = {
                        "type": "Inv-Ack",
                        "ack": 0,
                        "addr": addr,
                        "src": "node_" + str(self.cache_ID),
                        "dst": self.msgq_inv[0]["src"]
                    }
                    # Pop msg queue
                    self.msgq_inv.pop(0)
                    # update cache line
                    self.cache_dict[str(index_dec)]["protocol"] = "IM_AD"
                    if (self.print_flag): 
                        print("State Transition: SM_AD->IM_AD @ $-line-" + str(index_dec) + " with addr " + str(addr) + "!")
                elif (len(self.msgq_other) != 0) and (self.msgq_other[0]["addr"] == addr):
                    if(self.msgq_other[0]["type"] == "Inv-Ack"):
                        # Pop msg queue
                        self.msgq_other.pop(0)
                        # update CRHR
                        self.inv_ack_cnt += 1
                    elif (self.msgq_other[0]["type"] == "Data-FO"):
                        # Pop msg queue
                        self.msgq_other.pop(0)
                        # update cache line
                        self.cache_dict[str(index_dec)]["protocol"] = "M"
                        if (self.print_flag):
                            print("State Transition: SM_AD->M @ $-line-" + str(index_dec) + " with addr " + str(addr) + "!")
                        # update CRHR
                        self.CRHR = False
                    elif (self.msgq_other[0]["type"] == "Data-FD" and self.msgq_other[0]["ack"] == 0):
                        # Pop msg queue
                        self.msgq_other.pop(0)
                        # update cache line
                        self.cache_dict[str(index_dec)]["protocol"] = "M"
                        if (self.print_flag):
                            print("State Transition: SM_AD->M @ $-line-" + str(index_dec) + " with addr " + str(addr) + "!") 
                        # update CRHR
                        self.CRHR = False
                    elif (self.msgq_other[0]["type"] == "Data-FD" and self.msgq_other[0]["ack"] > 0):
                        # update CRHR
                        self.inv_ack = self.msgq_other[0]["ack"]
                        # Pop msg queue
                        self.msgq_other.pop(0)
                        # update cache line
                        self.cache_dict[str(index_dec)]["protocol"] = "SM_A"
                        if (self.print_flag):
                            print("State Transition: SM_AD->SM_A @ $-line-" + str(index_dec) + " with addr " + str(addr) + "!")
          # State: SM_A
            elif cache_line["protocol"] == "SM_A":
                if (self.inv_ack == self.inv_ack_cnt): # Already received enough ack during SM_AD
                    # update CRHR
                    self.inv_ack = 0
                    self.inv_ack_cnt = 0
                    self.CRHR = False
                    # update cache line
                    self.cache_dict[str(index_dec)]["protocol"] = "M"
                    if (self.print_flag):
                        print("State Transition: SM_A->M @ $-line-" + str(index_dec) + " with addr " + str(addr) + "!")
                elif (len(self.msgq_other) != 0) and (self.msgq_other[0]["type"] == "Inv-Ack") and (self.msgq_other[0]["addr"] == addr):
                    # Pop msg queue
                    self.msgq_other.pop(0)
                    # update CRHR
                    self.inv_ack_cnt += 1
                    if (self.inv_ack == self.inv_ack_cnt): # if Last Ack
                        # update CRHR
                        self.inv_ack = 0
                        self.inv_act_cnt = 0
                        self.CRHR = False
                        # update cache line
                        self.cache_dict[str(index_dec)]["protocol"] = "M"
                        if (self.print_flag):
                            print("State Transition: SM_A->M @ $-line-" + str(index_dec) + " with addr " + str(addr) + "!")
          # State: M
            elif cache_line["protocol"] == "M":
                if op == "ev":
                    # update output msg
                    self.msg_out = {
                        "type": "PutM",
                        "ack": 0,
                        "addr": addr,
                        "src": "node_" + str(self.cache_ID),
                        "dst": "dir"
                    }
                    # update cache line
                    self.cache_dict[str(index_dec)]["protocol"] = "MI_A"
                    if (self.print_flag): 
                        print("State Transition: M->MI_A @ $-line-" + str(index_dec) + " with addr " + str(addr) + "!")
                    # update CRHR
                    self.CRHR = True
                elif (len(self.msgq_fwd) != 0) and (self.msgq_fwd[0]["addr"] == addr):
                    if (self.msgq_fwd[0]["type"] == "Fwd-GetS"):
                        # update output msg
                        self.msg_out = {
                            "type": "Data-TRD",
                            "ack": 0,
                            "addr": addr,
                            "src": "node_" + str(self.cache_ID),
                            "dst": self.msgq_fwd[0]["req"]
                        }
                        # Pop msg queue
                        self.msgq_fwd.pop(0)
                        # update cache line
                        self.cache_dict[str(index_dec)]["protocol"] = "S"
                        if (self.print_flag): 
                            print("State Transition: M->S @ $-line-" + str(index_dec) + " with addr " + str(addr) + "!")
                    elif (self.msgq_fwd[0]["type"] == "Fwd-GetM"):
                       # update output msg
                        self.msg_out = {
                            "type": "Data-TR",
                            "ack": 0,
                            "addr": addr,
                            "src": "node_" + str(self.cache_ID),
                            "dst": self.msgq_fwd[0]["req"]
                        }
                        # Pop msg queue
                        self.msgq_fwd.pop(0)
                        # update cache line
                        self.cache_dict[str(index_dec)]["protocol"] = "I"
                        self.cache_dict[str(index_dec)]["addr"] = None
                        self.cache_dict[str(index_dec)]["tag"] = None
                        self.cache_dict[str(index_dec)]["index"] = None
                        self.cache_dict[str(index_dec)]["offset"] = None
                        if (self.print_flag): 
                            print("State Transition: M->I @ $-line-" + str(index_dec) + " with addr " + str(addr) + "!")
          # State: MI_A
            elif cache_line["protocol"] == "MI_A":
                if (len(self.msgq_fwd) != 0) and (self.msgq_fwd[0]["addr"] == addr):
                    if (self.msgq_fwd[0]["type"] == "Fwd-GetS"):
                        # update output msg
                        self.msg_out = {
                            "type": "Data-TRD",
                            "ack": 0,
                            "addr": addr,
                            "src": "node_" + str(self.cache_ID),
                            "dst": self.msgq_fwd[0]["req"]
                        }
                        # Pop msg queue
                        self.msgq_fwd.pop(0)
                        # update cache line
                        self.cache_dict[str(index_dec)]["protocol"] = "SI_A"
                        if (self.print_flag): 
                            print("State Transition: MI_A->SI_A @ $-line-" + str(index_dec) + " with addr " + str(addr) + "!")
                    elif (self.msgq_fwd[0]["type"] == "Fwd-GetM"):
                       # update output msg
                        self.msg_out = {
                            "type": "Data-TR",
                            "ack": 0,
                            "addr": addr,
                            "src": "node_" + str(self.cache_ID),
                            "dst": self.msgq_fwd[0]["req"]
                        }
                        # Pop msg queue
                        self.msgq_fwd.pop(0)
                        # update cache line
                        self.cache_dict[str(index_dec)]["protocol"] = "II_A"
                        if (self.print_flag): 
                            print("State Transition: MI_A->II_A @ $-line-" + str(index_dec) + " with addr " + str(addr) + "!")
                elif (len(self.msgq_other) != 0) and (self.msgq_other[0]["type"] == "Put-Ack") and (self.msgq_other[0]["addr"] == addr):
                    # Pop msg queue
                    self.msgq_other.pop(0)
                    # update cache line
                    self.cache_dict[str(index_dec)]["protocol"] = "I"
                    self.cache_dict[str(index_dec)]["addr"] = None
                    self.cache_dict[str(index_dec)]["tag"] = None
                    self.cache_dict[str(index_dec)]["index"] = None
                    self.cache_dict[str(index_dec)]["offset"] = None
                    if (self.print_flag): 
                        print("State Transition: MI_A->I @ $-line-" + str(index_dec) + " with addr " + str(addr) + "!")          
                    # update CRHR
                    self.CRHR = False
          # State: SI_A
            elif cache_line["protocol"] == "SI_A":
                if (len(self.msgq_inv) != 0) and (self.msgq_inv[0]["addr"] == addr):
                    # update output msg
                    self.msg_out = {
                        "type": "Inv-Ack",
                        "ack": 0,
                        "addr": addr,
                        "src": "node_" + str(self.cache_ID),
                        "dst": self.msgq_inv[0]["src"]
                    }
                    # Pop msg queue
                    self.msgq_inv.pop(0)
                    # update cache line
                    self.cache_dict[str(index_dec)]["protocol"] = "II_A"
                    if (self.print_flag): 
                        print("State Transition: SI_A->II_A @ $-line-" + str(index_dec) + " with addr " + str(addr) + "!")    
                elif (len(self.msgq_other) != 0) and (self.msgq_other[0]["type"] == "Put-Ack") and (self.msgq_other[0]["addr"] == addr):
                    # Pop msg queue
                    self.msgq_other.pop(0)
                    # update cache line
                    self.cache_dict[str(index_dec)]["protocol"] = "I"
                    self.cache_dict[str(index_dec)]["addr"] = None
                    self.cache_dict[str(index_dec)]["tag"] = None
                    self.cache_dict[str(index_dec)]["index"] = None
                    self.cache_dict[str(index_dec)]["offset"] = None
                    if (self.print_flag): 
                        print("State Transition: SI_A->I @ $-line-" + str(index_dec) + " with addr " + str(addr) + "!")          
                    # update CRHR
                    self.CRHR = False          
          # State: II_A
            elif cache_line["protocol"] == "II_A":
                if (len(self.msgq_other) != 0) and (self.msgq_other[0]["type"] == "Put-Ack") and (self.msgq_other[0]["addr"] == addr):
                    # Pop msg queue
                    self.msgq_other.pop(0)
                    # update cache line
                    self.cache_dict[str(index_dec)]["protocol"] = "I"
                    self.cache_dict[str(index_dec)]["addr"] = None
                    self.cache_dict[str(index_dec)]["tag"] = None
                    self.cache_dict[str(index_dec)]["index"] = None
                    self.cache_dict[str(index_dec)]["offset"] = None
                    if (self.print_flag): 
                        print("State Transition: II_A->I @ $-line-" + str(index_dec) + " with addr " + str(addr) + "!")          
                    # update CRHR
                    self.CRHR = False   
             
      # Then handle incoming Fwd and Inv messages out of attention
        # default empty output message
        self.msg_out_ch2 = {
            "type": "None",
            "ack": 0,
            "addr": 0,
            "src": "node_" + str(self.cache_ID),
            "dst": "dir"
        }
    
    # MESI cache coherence protocol controller
    def cache_ctrl_mesi(self):
        pass
    
    # MOSI cache coherence protocol controller
    def cache_ctrl_mosi(self):
        pass