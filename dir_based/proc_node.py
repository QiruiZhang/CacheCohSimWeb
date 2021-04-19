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
                                           "tag": None, # binary tag
                                           "index": None, # local cache block index, decimal
                                           "offset": None, # not used
                                           "protocol": "I"}
        else:
            self.cache_dict = file

    # transfer decimal to binary and pad with zero
    def decimal2binary(self, num, bits):
        binary = bin(num)[2:].zfill(bits)
        return binary
    
    '''
    def print_cache(self):
        for key, val in self.cache_dict.items():
            print(f"line[{key}] = {val}")
    '''

    def return_cache_dict(self):
        return {self.cache_ID: {"cache": self.cache_dict, "LSR": self.line_queue}}

# Processor node class inherited from cache: core + cache + cache-ctrl + msg-queues
class proc_node(cache):
    # Object initialization
    def __init__(self, ID, inst = [], protocol = 'MSI', size = 128, line_size = 8, mem_size = 512, LSR = [], print_flag = True):
        super().__init__(str(ID), size, line_size, mem_size, None, LSR) # Inheritance
        self.print_flag = print_flag
        self.insts = inst # Input instructions from user
        self.protocol = protocol # Protocol type: MSI, MESI or MOSI

        self.PC = 0 # PC is only accumulated when processor is not stalled        
        self.CRHR_inst = ["nop", 0]
        self.CRHR = False # Coherence Request Handling Register
        self.ack_cnt = 0
        self.ack_needed = 0
        
        self.msgq_fwd = [] # Input msg queue/channel for forwarded msgs
        self.msgq_inv = [] # Input msg queue/channel for invalidations
        self.msgq_resp = [] # Input msg queue/channel for other msgs
        self.msgq_out = [] # Output msg queue. Multiple output messages may be generated within a logical cycle
        self.msg_out = {
            "type": "None",
            "ack": 0, # Used only when type is Data-FD (Data from Directory)
            "dirblk": 0, # Cache block index in directory
            "addr": 0, # Addr from instructions
            "src": "node_" + str(ID),
            "dst": "dir",
            "req": None
        } # Output msg updated per cycle for addr-of-attention

        ''' Message Types
            Dir->node message types:
                Fwd-GetS
                Fwd-GetM
                Inv
                Put-Ack
                Data-FD (Data from Dir)
                
            node->Dir message types:
                GetS
                GetM
                PutS
                PutM
                Data-TD (Data to Dir)
                Fwd-Ack

            node<->node message types:
                Data-FO (Data from Owner)
                Inv-Ack
        '''

        self.node_log = []

    def proc_reset(self):
        # Reset dict
        for i in range(self.cache_num_line):
            self.cache_dict[str(i)] = {
                "addr": None,
                "tag": None, # binary tag
                "index": None, # local cache block index, decimal
                "offset": None, # not used
                "protocol": "I"
            }

        # Reset PC and CRHR
        self.PC = 0        
        self.CRHR_inst = ["nop", 0]
        self.CRHR = False
        self.ack_cnt = 0
        self.ack_needed = 0
        
        # Reset Queues
        self.msgq_fwd = []
        self.msgq_inv = []
        self.msgq_resp = []
        self.msgq_out = []

        # Reset Log
        self.node_log = []

    # Input messages into the queues, used by simulator main program
    def input_msg(self, msg):
        if msg['type'] == 'Fwd-GetS' or msg['type'] == 'Fwd-GetM':
            self.msgq_fwd.append(msg)
        elif msg['type'] == 'Inv':
            self.msgq_inv.append(msg)
        else:
            self.msgq_resp.append(msg)
    
    # Get message output of the current cycle
    def output_msg(self):
        return self.msgq_out.pop(0)
    
    def addrToCacheInd(self, addr):
        addr_bin = self.decimal2binary(addr, self.addr_bits)
        index_bits  = int(math.log2(self.cache_num_line))
        offset_bits = int(math.log2(self.cache_line_size))
        tag_bits    = self.addr_bits - index_bits - offset_bits
        tag    = addr_bin[0:tag_bits]
        index  = addr_bin[tag_bits:(self.addr_bits - offset_bits)]
        return (tag, int(index, 2)) # Cache block index in the local cache
        
    def addrToDirInd(self, addr):
        addr_bin = self.decimal2binary(addr, self.addr_bits)
        offset_bits = int(math.log2(self.cache_line_size))
        dir_index  = addr_bin[0:(self.addr_bits - offset_bits)]
        return int(dir_index, 2)
    
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
        self.node_log = []

        # 0. PC and End of Program
        eop_flag = False
        if (not self.CRHR):
            # Check end of program
            if (self.PC >= len(self.insts)):
                log = "End of node_" + str(self.cache_ID) + " program!"
                self.node_log.append(log)
                if (self.print_flag):
                    print(log)
                eop_flag = True
            else:
                self.CRHR_inst = self.insts[self.PC]
                self.PC += 1
                eop_flag = False
        
        # 1. Handle processor-side instructions
        inst_processed = False
        if (not self.CRHR) and (not eop_flag):
            op = self.CRHR_inst[0]
            addr = self.CRHR_inst[1]

            # Setup tag and index
            (tag, index_dec) = self.addrToCacheInd(addr)
            cache_line = self.cache_dict[str(index_dec)]
            DirInd_dec = self.addrToDirInd(addr) # Cache block index in the directory
        
            # State I
            if cache_line["protocol"] == "I":
                if op == "ld": # Send GetS to Dir/IS_D
                    # update output msg
                    self.msg_out = {
                        "type": "GetS",
                        "ack": 0,
                        "dirblk": DirInd_dec,
                        "addr": addr,
                        "src": "node_" + str(self.cache_ID),
                        "dst": "dir",
                        "req": "node_" + str(self.cache_ID)
                        }
                    self.msgq_out.append(self.msg_out)

                    # update cache line
                    self.cache_dict[str(index_dec)]["protocol"] = "IS_D"
                    self.cache_dict[str(index_dec)]["addr"] = addr
                    self.cache_dict[str(index_dec)]["tag"] = tag
                    self.cache_dict[str(index_dec)]["index"] = index_dec
                    self.cache_dict[str(index_dec)]["offset"] = None
                    
                    # Update log
                    log = "State transition I->IS_D @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!"
                    self.node_log.append(log)
                    if (self.print_flag): 
                        print(log)
                    
                    # update CRHR
                    self.CRHR = True
                    inst_processed = True
                elif op == "st": # Send GetM to Dir/IM_AD
                    # update output msg
                    self.msg_out = {
                        "type": "GetM",
                        "ack": 0,
                        "dirblk": DirInd_dec,
                        "addr": addr,
                        "src": "node_" + str(self.cache_ID),
                        "dst": "dir",
                        "req": "node_" + str(self.cache_ID)
                    }    
                    self.msgq_out.append(self.msg_out)

                    # update cache line
                    self.cache_dict[str(index_dec)]["protocol"] = "IM_AD"
                    self.cache_dict[str(index_dec)]["addr"] = addr
                    self.cache_dict[str(index_dec)]["tag"] = tag
                    self.cache_dict[str(index_dec)]["index"] = index_dec
                    self.cache_dict[str(index_dec)]["offset"] = None

                    # Update log
                    log = "State transition I->IM_AD @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!"
                    self.node_log.append(log)
                    if (self.print_flag): 
                        print(log)

                    # update CRHR
                    self.CRHR = True
                    inst_processed = True
            # State: S
            elif cache_line["protocol"] == "S":
                if op == "ld":
                    self.cache_dict[str(index_dec)]["addr"] = addr
                    # Update log
                    log = "Cache hit of Load @ $-line-" + str(index_dec) + ", addr-" + str(addr) + "!"
                    self.node_log.append(log)
                    if (self.print_flag): 
                        print(log)  

                    # Update CRHR
                    inst_processed = True
                elif op == "st":
                    # update output msg
                    self.msg_out = {
                        "type": "GetM",
                        "ack": 0,
                        "dirblk": DirInd_dec,
                        "addr": addr,
                        "src": "node_" + str(self.cache_ID),
                        "dst": "dir",
                        "req": "node_" + str(self.cache_ID)
                    }
                    self.msgq_out.append(self.msg_out)
                    
                    # update cache line
                    self.cache_dict[str(index_dec)]["protocol"] = "SM_AD"
                    self.cache_dict[str(index_dec)]["addr"] = addr
                    self.cache_dict[str(index_dec)]["tag"] = tag
                    self.cache_dict[str(index_dec)]["index"] = index_dec
                    self.cache_dict[str(index_dec)]["offset"] = None
                  
                    # Update log
                    log = "State transition S->SM_AD @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!"
                    self.node_log.append(log)
                    if (self.print_flag): 
                        print(log) 

                    # update CRHR
                    self.CRHR = True
                    inst_processed = True
                elif op == "ev":
                    # update output msg
                    self.msg_out = {
                        "type": "PutS",
                        "ack": 0,
                        "dirblk": DirInd_dec,
                        "addr": addr,
                        "src": "node_" + str(self.cache_ID),
                        "dst": "dir",
                        "req": None
                    }
                    self.msgq_out.append(self.msg_out)
                    
                    # update cache line
                    self.cache_dict[str(index_dec)]["addr"] = addr
                    self.cache_dict[str(index_dec)]["protocol"] = "SI_A"

                    # Update log
                    log = "State transition S->SI_A @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!"
                    self.node_log.append(log)
                    if (self.print_flag): 
                        print(log) 
                    
                    # update CRHR
                    self.CRHR = True
                    inst_processed = True
            # State: SM_AD
            elif cache_line["protocol"] == "SM_AD":
                if op == "ld":
                    self.cache_dict[str(index_dec)]["addr"] = addr
                    # Update log
                    log = "Cache hit of Load @ $-line-" + str(index_dec) + ", addr-" + str(addr) + "!"
                    self.node_log.append(log)
                    if (self.print_flag): 
                        print(log)  

                    # Update CRHR
                    inst_processed = True
            # State: SM_A
            elif cache_line["protocol"] == "SM_A":
                if op == "ld":
                    self.cache_dict[str(index_dec)]["addr"] = addr
                    # Update log
                    log = "Cache hit of Load @ $-line-" + str(index_dec) + ", addr-" + str(addr) + "!"
                    self.node_log.append(log)
                    if (self.print_flag): 
                        print(log)  

                    # Update CRHR
                    inst_processed = True
            # State: M
            elif cache_line["protocol"] == "M":
                if op == "ld":
                    self.cache_dict[str(index_dec)]["addr"] = addr
                    # Update log
                    log = "Cache hit of Load @ $-line-" + str(index_dec) + ", addr-" + str(addr) + "!"
                    self.node_log.append(log)
                    if (self.print_flag): 
                        print(log)  

                    # Update CRHR
                    inst_processed = True
                elif op == "st":
                    self.cache_dict[str(index_dec)]["addr"] = addr
                    # Update log
                    log = "Cache hit of Store @ $-line-" + str(index_dec) + ", addr-" + str(addr) + "!"
                    self.node_log.append(log)
                    if (self.print_flag): 
                        print(log)  

                    # Update CRHR
                    inst_processed = True
                elif op == "ev":
                    # update output msg
                    self.msg_out = {
                        "type": "PutM",
                        "ack": 0,
                        "dirblk": DirInd_dec,
                        "addr": addr,
                        "src": "node_" + str(self.cache_ID),
                        "dst": "dir",
                        "req": None
                    }
                    self.msgq_out.append(self.msg_out)
                    
                    # update cache line
                    self.cache_dict[str(index_dec)]["addr"] = addr
                    self.cache_dict[str(index_dec)]["protocol"] = "MI_A"
                    
                    # Update log
                    log = "State transition M->MI_A @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!"
                    self.node_log.append(log)
                    if (self.print_flag): 
                        print(log)  

                    # update CRHR
                    self.CRHR = True
                    inst_processed = True
            else:
                pass

        # 2. Handle Fwd Input Msg Queue
        msgq_fwd_popped = False
        if (not inst_processed) and (len(self.msgq_fwd) != 0):
            head_msg = self.msgq_fwd[0]
            DirInd_dec = head_msg["dirblk"]
            index_dec = DirInd_dec % self.cache_num_line
            cache_line = self.cache_dict[str(index_dec)]
            
            # State: M
            if cache_line["protocol"] == "M":
                if (head_msg["type"] == "Fwd-GetS"):
                    # update output msg
                    self.msg_out = {
                        "type": "Data-FO",
                        "ack": 0,
                        "dirblk": DirInd_dec,
                        "addr": head_msg["addr"],
                        "src": "node_" + str(self.cache_ID),
                        "dst": head_msg["req"],
                        "req": None
                    }
                    self.msgq_out.append(self.msg_out)

                    self.msg_out = {
                        "type": "Data-TD",
                        "ack": 0,
                        "dirblk": DirInd_dec,
                        "addr": head_msg["addr"],
                        "src": "node_" + str(self.cache_ID),
                        "dst": "dir",
                        "req": None
                    }
                    self.msgq_out.append(self.msg_out)
                    
                    # update cache line
                    self.cache_dict[str(index_dec)]["protocol"] = "S"

                    # Update log
                    log = "State transition M->S @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!"
                    self.node_log.append(log)
                    if (self.print_flag): 
                        print(log) 

                    # Pop msg queue
                    self.msgq_fwd.pop(0)
                    msgq_fwd_popped = True
                elif (head_msg["type"] == "Fwd-GetM"):
                    # update output msg
                    self.msg_out = {
                        "type": "Data-FO",
                        "ack": 0,
                        "dirblk": DirInd_dec,
                        "addr": head_msg["addr"],
                        "src": "node_" + str(self.cache_ID),
                        "dst": head_msg["req"],
                        "req": None
                    }
                    self.msgq_out.append(self.msg_out)

                    self.msg_out = {
                        "type": "Fwd-Ack",
                        "ack": 0,
                        "dirblk": DirInd_dec,
                        "addr": head_msg["addr"],
                        "src": "node_" + str(self.cache_ID),
                        "dst": "dir",
                        "req": None
                    }
                    self.msgq_out.append(self.msg_out)

                    # update cache line
                    self.cache_dict[str(index_dec)]["protocol"] = "I"
                    self.cache_dict[str(index_dec)]["addr"] = None
                    self.cache_dict[str(index_dec)]["tag"] = None
                    self.cache_dict[str(index_dec)]["index"] = None
                    self.cache_dict[str(index_dec)]["offset"] = None
                    
                    # Update log
                    log = "State transition M->I @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!"
                    self.node_log.append(log)
                    if (self.print_flag): 
                        print(log) 

                    # Pop msg queue
                    self.msgq_fwd.pop(0)
                    msgq_fwd_popped = True
            # State: MI_A
            elif cache_line["protocol"] == "MI_A":
                if (head_msg["type"] == "Fwd-GetS"):
                    # update output msg
                    self.msg_out = {
                        "type": "Data-FO",
                        "ack": 0,
                        "dirblk": DirInd_dec,
                        "addr": head_msg["addr"],
                        "src": "node_" + str(self.cache_ID),
                        "dst": head_msg["req"],
                        "req": None
                    }
                    self.msgq_out.append(self.msg_out)

                    self.msg_out = {
                        "type": "Data-TD",
                        "ack": 0,
                        "dirblk": DirInd_dec,
                        "addr": head_msg["addr"],
                        "src": "node_" + str(self.cache_ID),
                        "dst": "dir",
                        "req": None
                    }
                    self.msgq_out.append(self.msg_out)
                    
                    # update cache line
                    self.cache_dict[str(index_dec)]["protocol"] = "SI_A"

                    # Update log
                    log = "State transition MI_A->SI_A @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!"
                    self.node_log.append(log)
                    if (self.print_flag): 
                        print(log) 

                    # Pop msg queue
                    self.msgq_fwd.pop(0)
                    msgq_fwd_popped = True
                elif (head_msg["type"] == "Fwd-GetM"):
                    # update output msg
                    self.msg_out = {
                        "type": "Data-FO",
                        "ack": 0,
                        "dirblk": DirInd_dec,
                        "addr": head_msg["addr"],
                        "src": "node_" + str(self.cache_ID),
                        "dst": head_msg["req"],
                        "req": None
                    }
                    self.msgq_out.append(self.msg_out)

                    self.msg_out = {
                        "type": "Fwd-Ack",
                        "ack": 0,
                        "dirblk": DirInd_dec,
                        "addr": head_msg["addr"],
                        "src": "node_" + str(self.cache_ID),
                        "dst": "dir",
                        "req": None
                    }
                    self.msgq_out.append(self.msg_out)

                    # update cache line
                    self.cache_dict[str(index_dec)]["protocol"] = "II_A"
                    
                    # Update log
                    log = "State transition MI_A->II_A @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!"
                    self.node_log.append(log)
                    if (self.print_flag): 
                        print(log) 

                    # Pop msg queue
                    self.msgq_fwd.pop(0)
                    msgq_fwd_popped = True
            else:
                pass

        # 3. Handle Inv Input Msg Queue    
        msgq_inv_popped = False        
        if (not inst_processed) and (not msgq_fwd_popped) and (len(self.msgq_inv) != 0):
            head_msg = self.msgq_inv[0]
            DirInd_dec = head_msg["dirblk"]
            index_dec = DirInd_dec % self.cache_num_line
            cache_line = self.cache_dict[str(index_dec)]

            # State: S
            if cache_line["protocol"] == "S":
                # update output msg
                self.msg_out = {
                    "type": "Inv-Ack",
                    "ack": 0,
                    "dirblk": DirInd_dec,
                    "addr": head_msg["addr"],
                    "src": "node_" + str(self.cache_ID),
                    "dst": head_msg["req"],
                    "req": None
                }
                self.msgq_out.append(self.msg_out)

                self.msg_out = {
                    "type": "Inv-Ack",
                    "ack": 0,
                    "dirblk": DirInd_dec,
                    "addr": head_msg["addr"],
                    "src": "node_" + str(self.cache_ID),
                    "dst": "dir",
                    "req": None
                }
                self.msgq_out.append(self.msg_out)

                # update cache line
                self.cache_dict[str(index_dec)]["protocol"] = "I"
                self.cache_dict[str(index_dec)]["addr"] = None
                self.cache_dict[str(index_dec)]["tag"] = None
                self.cache_dict[str(index_dec)]["index"] = None
                self.cache_dict[str(index_dec)]["offset"] = None
                
                # Update log
                log = "State transition S->I @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!"
                self.node_log.append(log)
                if (self.print_flag): 
                    print(log) 
                
                # Pop msg queue
                self.msgq_inv.pop(0)
                msgq_inv_popped = True
            # State: SM_AD
            elif cache_line["protocol"] == "SM_AD":
                # update output msg
                self.msg_out = {
                    "type": "Inv-Ack",
                    "ack": 0,
                    "dirblk": DirInd_dec,
                    "addr": head_msg["addr"],
                    "src": "node_" + str(self.cache_ID),
                    "dst": head_msg["req"],
                    "req": None
                }
                self.msgq_out.append(self.msg_out)

                self.msg_out = {
                    "type": "Inv-Ack",
                    "ack": 0,
                    "dirblk": DirInd_dec,
                    "addr": head_msg["addr"],
                    "src": "node_" + str(self.cache_ID),
                    "dst": "dir",
                    "req": None
                }
                self.msgq_out.append(self.msg_out)

                # update cache line
                self.cache_dict[str(index_dec)]["protocol"] = "IM_AD"
                
                # Update log
                log = "State transition SM_AD->IM_AD @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!"
                self.node_log.append(log)
                if (self.print_flag): 
                    print(log) 
                
                # Pop msg queue
                self.msgq_inv.pop(0)
                msgq_inv_popped = True           
            # State: SI_A  
            elif cache_line["protocol"] == "SI_A":
                # update output msg
                self.msg_out = {
                    "type": "Inv-Ack",
                    "ack": 0,
                    "dirblk": DirInd_dec,
                    "addr": head_msg["addr"],
                    "src": "node_" + str(self.cache_ID),
                    "dst": head_msg["req"],
                    "req": None
                }
                self.msgq_out.append(self.msg_out)

                self.msg_out = {
                    "type": "Inv-Ack",
                    "ack": 0,
                    "dirblk": DirInd_dec,
                    "addr": head_msg["addr"],
                    "src": "node_" + str(self.cache_ID),
                    "dst": "dir",
                    "req": None
                }
                self.msgq_out.append(self.msg_out)

                # update cache line
                self.cache_dict[str(index_dec)]["protocol"] = "II_A"

                # Update log
                log = "State transition SI_A->II_A @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!"
                self.node_log.append(log)
                if (self.print_flag): 
                    print(log) 
                
                # Pop msg queue
                self.msgq_inv.pop(0)
                msgq_inv_popped = True
            else:
                pass

        # 4. Handle Response Input Msg Queue
        if (not inst_processed) and (not msgq_fwd_popped) and (not msgq_inv_popped) and (len(self.msgq_resp) != 0):
            head_msg = self.msgq_resp[0]
            DirInd_dec = head_msg["dirblk"]
            index_dec = DirInd_dec % self.cache_num_line
            cache_line = self.cache_dict[str(index_dec)]

            # State: IS_D
            if cache_line["protocol"] == "IS_D":
                if (head_msg["type"] == "Data-FO"):
                    # update cache line
                    self.cache_dict[str(index_dec)]["protocol"] = "S"
                    
                    # Update log
                    log = "State transition IS_D->S @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!"
                    self.node_log.append(log)
                    if (self.print_flag): 
                        print(log) 
                    
                    # Pop msg queue
                    self.msgq_resp.pop(0)

                    # update CRHR
                    self.CRHR = False
                elif (head_msg["type"] == "Data-FD" and head_msg["ack"] == 0):
                    # update cache line
                    self.cache_dict[str(index_dec)]["protocol"] = "S"
                    
                    # Update log
                    log = "State transition IS_D->S @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!"
                    self.node_log.append(log)
                    if (self.print_flag): 
                        print(log) 
                    
                    # Pop msg queue
                    self.msgq_resp.pop(0)

                    # update CRHR
                    self.CRHR = False
            # State: IM_AD
            elif cache_line["protocol"] == "IM_AD":
                if(head_msg["type"] == "Inv-Ack"):
                    # Pop msg queue
                    self.msgq_resp.pop(0)

                    # update CRHR
                    self.ack_cnt += 1
                elif (head_msg["type"] == "Data-FO"):
                    # update cache line
                    self.cache_dict[str(index_dec)]["protocol"] = "M"

                    # Update log
                    log = "State transition IM_AD->M @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!"
                    self.node_log.append(log)
                    if (self.print_flag): 
                        print(log) 

                    # Pop msg queue
                    self.msgq_resp.pop(0)

                    # update CRHR
                    self.CRHR = False
                elif (head_msg["type"] == "Data-FD" and head_msg["ack"] == 0):
                    # update cache line
                    self.cache_dict[str(index_dec)]["protocol"] = "M"

                    # Update log
                    log = "State transition IM_AD->M @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!"
                    self.node_log.append(log)
                    if (self.print_flag): 
                        print(log) 

                    # Pop msg queue
                    self.msgq_resp.pop(0)

                    # update CRHR
                    self.CRHR = False
                elif (head_msg["type"] == "Data-FD" and head_msg["ack"] > 0):
                    self.ack_needed = head_msg["ack"]
                    if (self.ack_cnt == self.ack_needed):
                        # update cache line
                        self.cache_dict[str(index_dec)]["protocol"] = "M"

                        # Update log
                        log = "State transition IM_AD->M @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!"
                        self.node_log.append(log)
                        if (self.print_flag): 
                            print(log) 

                        # update CRHR
                        self.ack_cnt = 0
                        self.ack_needed = 0
                        self.CRHR = False
                    else:
                        # update cache line
                        self.cache_dict[str(index_dec)]["protocol"] = "IM_A"

                        # Update log
                        log = "State transition IM_AD->IM_A @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!"
                        self.node_log.append(log)
                        if (self.print_flag): 
                            print(log) 

                    # Pop msg queue
                    self.msgq_resp.pop(0)   
            # State: IM_A
            elif cache_line["protocol"] == "IM_A":
                if (head_msg["type"] == "Inv-Ack"):
                    self.ack_cnt += 1
                    if (self.ack_cnt == self.ack_needed): # if Last Ack
                        # update cache line
                        self.cache_dict[str(index_dec)]["protocol"] = "M"
                        
                        # Update log
                        log = "State transition IM_A->M @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!"
                        self.node_log.append(log)
                        if (self.print_flag): 
                            print(log) 

                        # update CRHR
                        self.ack_cnt = 0
                        self.ack_needed = 0
                        self.CRHR = False

                    # Pop msg queue
                    self.msgq_resp.pop(0)
            # State: SM_AD
            elif cache_line["protocol"] == "SM_AD":
                if(head_msg["type"] == "Inv-Ack"):
                    # Pop msg queue
                    self.msgq_resp.pop(0)

                    # update CRHR
                    self.ack_cnt += 1
                elif (head_msg["type"] == "Data-FO"):
                    # update cache line
                    self.cache_dict[str(index_dec)]["protocol"] = "M"

                    # Update log
                    log = "State transition SM_AD->M @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!"
                    self.node_log.append(log)
                    if (self.print_flag): 
                        print(log) 

                    # Pop msg queue
                    self.msgq_resp.pop(0)

                    # update CRHR
                    self.CRHR = False
                elif (head_msg["type"] == "Data-FD" and head_msg["ack"] == 0):
                    # update cache line
                    self.cache_dict[str(index_dec)]["protocol"] = "M"

                    # Update log
                    log = "State transition SM_AD->M @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!"
                    self.node_log.append(log)
                    if (self.print_flag): 
                        print(log) 

                    # Pop msg queue
                    self.msgq_resp.pop(0)

                    # update CRHR
                    self.CRHR = False
                elif (head_msg["type"] == "Data-FD" and head_msg["ack"] > 0):
                    self.ack_needed = head_msg["ack"]
                    if (self.ack_cnt == self.ack_needed):
                        # update cache line
                        self.cache_dict[str(index_dec)]["protocol"] = "M"

                        # Update log
                        log = "State transition SM_AD->M @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!"
                        self.node_log.append(log)
                        if (self.print_flag): 
                            print(log) 

                        # update CRHR
                        self.ack_cnt = 0
                        self.ack_needed = 0
                        self.CRHR = False
                    else:
                        # update cache line
                        self.cache_dict[str(index_dec)]["protocol"] = "SM_A"

                        # Update log
                        log = "State transition SM_AD->SM_A @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!"
                        self.node_log.append(log)
                        if (self.print_flag): 
                            print(log) 

                    # Pop msg queue
                    self.msgq_resp.pop(0)  
            # State: SM_A
            elif cache_line["protocol"] == "SM_A":
                if (head_msg["type"] == "Inv-Ack"):
                    self.ack_cnt += 1
                    if (self.ack_cnt == self.ack_needed): # if Last Ack
                        # update cache line
                        self.cache_dict[str(index_dec)]["protocol"] = "M"
                        
                        # Update log
                        log = "State transition SM_A->M @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!"
                        self.node_log.append(log)
                        if (self.print_flag): 
                            print(log) 

                        # update CRHR
                        self.ack_cnt = 0
                        self.ack_needed = 0
                        self.CRHR = False

                    # Pop msg queue
                    self.msgq_resp.pop(0)
            # State: MI_A
            elif cache_line["protocol"] == "MI_A":
                if (head_msg["type"] == "Put-Ack"):
                    # update cache line
                    self.cache_dict[str(index_dec)]["protocol"] = "I"
                    self.cache_dict[str(index_dec)]["addr"] = None
                    self.cache_dict[str(index_dec)]["tag"] = None
                    self.cache_dict[str(index_dec)]["index"] = None
                    self.cache_dict[str(index_dec)]["offset"] = None
                    
                    # Update log
                    log = "State transition MI_A->I @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!"
                    self.node_log.append(log)
                    if (self.print_flag): 
                        print(log)

                    # Pop msg queue
                    self.msgq_resp.pop(0) 
                    
                    # update CRHR
                    self.CRHR = False
            # State: SI_A
            elif cache_line["protocol"] == "SI_A":
                if (head_msg["type"] == "Put-Ack"):
                    # update cache line
                    self.cache_dict[str(index_dec)]["protocol"] = "I"
                    self.cache_dict[str(index_dec)]["addr"] = None
                    self.cache_dict[str(index_dec)]["tag"] = None
                    self.cache_dict[str(index_dec)]["index"] = None
                    self.cache_dict[str(index_dec)]["offset"] = None
                    
                    # Update log
                    log = "State transition SI_A->I @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!"
                    self.node_log.append(log)
                    if (self.print_flag): 
                        print(log)

                    # Pop msg queue
                    self.msgq_resp.pop(0) 
                    
                    # update CRHR
                    self.CRHR = False        
            # State: II_A
            elif cache_line["protocol"] == "II_A":
                if (head_msg["type"] == "Put-Ack"):
                    # update cache line
                    self.cache_dict[str(index_dec)]["protocol"] = "I"
                    self.cache_dict[str(index_dec)]["addr"] = None
                    self.cache_dict[str(index_dec)]["tag"] = None
                    self.cache_dict[str(index_dec)]["index"] = None
                    self.cache_dict[str(index_dec)]["offset"] = None
                    
                    # Update log
                    log = "State transition II_A->I @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!"
                    self.node_log.append(log)
                    if (self.print_flag): 
                        print(log)

                    # Pop msg queue
                    self.msgq_resp.pop(0) 
                    
                    # update CRHR
                    self.CRHR = False
            else:
                pass
        
    # MESI cache coherence protocol controller
    def cache_ctrl_mesi(self):
        pass
    
    # MOSI cache coherence protocol controller
    def cache_ctrl_mosi(self):
        pass