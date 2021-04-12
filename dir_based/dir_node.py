# -*- coding: utf-8 -*-
import math

# Directory Node Class
class dir_node():
    def __init__(self, protocol = 'MSI', line_size = 8, mem_size = 512, dir_file = None, print_flag = True):
        self.mem_size = mem_size # Bytes
        self.dir_line_size = line_size #Bytes
        self.dir_dict = {}
        self.addr_bits = int(math.log2(mem_size))
        self.dir_num_line = int(mem_size/line_size)
                
        self.print_flag = print_flag
        
        self.protocol = protocol # Protocol type: MSI, MESI or MOSI
                
        self.inv_ack_cnt = 0
        self.inv_ack = 0
        
        self.msgq_req = [] # Input msg queue/channel for requests
        self.msgq_resp = [] # Input msg queue/channel for responses
    
        self.msgq_out = [] # Output msg queue. Multiple output messages may be generated within a logical cycle
        self.msg_out = {
            "type": "None",
            "ack": 0, # Used only when type is Data-FD (Data from Directory)
            "dirblk": 0, # Cache block index in directory
            "src": "dir",
            "dst": "node_0",
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
                
            node<->node message types:
                Data-FO (Data from Owner)
                Inv-Ack
        '''

        if dir_file == None:
            for i in range(self.dir_num_line):
                self.dir_dict[str(i)] = {"addr": None, # directory block index, decimal
                                         "tag": None, # binary tag
                                         "index": None, # local cache block index, decimal
                                         "offset": None, # not used
                                         "protocol": "I"}
        else:
            self.dir_dict = dir_file

    # transfer decimal to binary and pad with zero
    def decimal2binary(self, num, bits):
        binary = bin(num)[2:].zfill(bits)
        return binary

    def print_dir(self):
        for key, val in self.dir_dict.items():
            print(f"line[{key}] = {val}")

    def return_dir_dict(self):
        return {"dir": self.dir_dict}
          
    # Input messages into the queues, used by simulator main program
    def input_msg(self, msg):
        if msg['type'] == 'Data-TD':
            self.msgq_resp.append(msg)
        else:
            self.msgq_req.append(msg)
    
    # Get message output of the current cycle
    def output_msg(self):
        # return [self.msg_out, self.msg_out_ch2]
        return self.msgq_out.pop(0)
        
    # Update the directory node state by one cycle
    def dir_run(self):
        if self.protocol == 'MSI':
            self.dir_ctrl_msi()
        elif self.protocol == 'MESI':
            self.dir_ctrl_mesi()
        elif self.protocol == 'MOSI':
            self.dir_ctrl_mosi()
        else:
            pass
    
    # MSI directory controller
    def dir_ctrl_msi(self):     
      # First handle processor-side instructions
        eop_flag = False
        if (not self.CRHR):
            # Check end of program
            if (self.PC >= len(self.insts)):
                print("End of node_" + str(self.cache_ID) + " program!")
                #return
                eop_flag = True
            else:
                self.CRHR_inst = self.insts[self.PC]
                self.PC += 1
                eop_flag = False
        op = self.CRHR_inst[0]
        addr = self.CRHR_inst[1]
        
        # Setup tag and index
        (tag, index_dec) = self.addrToCacheInd(addr)
        cache_line = self.cache_dict[str(index_dec)]
        DirInd_dec = self.addrToDirInd(addr) # Cache block index in the directory
        
        # Finite State Machine from ch8 of 'A Primer on Memory Consistency and Cache Coherence'
        if (op != "nop") and (not eop_flag): # only attend to the instruction when it is not no-op
          # State: I
            if cache_line["protocol"] == "I":
                if op == "ld": # Send GetS to Dir/IS_D
                    # update output msg
                    self.msg_out = {
                        "type": "GetS",
                        "ack": 0,
                        "dirblk": DirInd_dec,
                        "src": "node_" + str(self.cache_ID),
                        "dst": "dir",
                        "req": "node_" + str(self.cache_ID)
                        }
                    self.msgq_out.append(self.msg_out)
                    # update cache line
                    self.cache_dict[str(index_dec)]["protocol"] = "IS_D"
                    self.cache_dict[str(index_dec)]["addr"] = DirInd_dec
                    self.cache_dict[str(index_dec)]["tag"] = tag
                    self.cache_dict[str(index_dec)]["index"] = index_dec
                    self.cache_dict[str(index_dec)]["offset"] = None
                    if (self.print_flag): 
                        print("State Transition: I->IS_D @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!")
                    # update CRHR
                    self.CRHR = True
                elif op == "st": # Send GetM to Dir/IM_AD
                    # update output msg
                    self.msg_out = {
                        "type": "GetM",
                        "ack": 0,
                        "dirblk": DirInd_dec,
                        "src": "node_" + str(self.cache_ID),
                        "dst": "dir",
                        "req": "node_" + str(self.cache_ID)
                    }    
                    self.msgq_out.append(self.msg_out)
                    # update cache line
                    self.cache_dict[str(index_dec)]["protocol"] = "IM_AD"
                    self.cache_dict[str(index_dec)]["addr"] = DirInd_dec
                    self.cache_dict[str(index_dec)]["tag"] = tag
                    self.cache_dict[str(index_dec)]["index"] = index_dec
                    self.cache_dict[str(index_dec)]["offset"] = None
                    if (self.print_flag): 
                        print("State Transition: I->IM_AD @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!")
                    # update CRHR
                    self.CRHR = True
          # State: IS_D
            elif cache_line["protocol"] == "IS_D":
                if (len(self.msgq_other) != 0) and (self.msgq_other[0]["type"] == "Data-FD" or self.msgq_other[0]["type"] == "Data-FO") and (self.msgq_other[0]["dirblk"] == DirInd_dec):
                    # Pop msg queue
                    self.msgq_other.pop(0)
                    # update cache line
                    self.cache_dict[str(index_dec)]["protocol"] = "S"
                    if (self.print_flag):
                        print("State Transition: IS_D->S @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!")
                    # update CRHR
                    self.CRHR = False
          # State: IM_AD
            elif cache_line["protocol"] == "IM_AD":
                if (len(self.msgq_other) != 0) and (self.msgq_other[0]["dirblk"] == DirInd_dec):
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
                            print("State Transition: IM_AD->M @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!")
                        # update CRHR
                        self.CRHR = False
                    elif (self.msgq_other[0]["type"] == "Data-FD" and self.msgq_other[0]["ack"] == 0):
                        # Pop msg queue
                        self.msgq_other.pop(0)
                        # update cache line
                        self.cache_dict[str(index_dec)]["protocol"] = "M"
                        if (self.print_flag):
                            print("State Transition: IM_AD->M @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!") 
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
                            print("State Transition: IM_AD->IM_A @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!")    
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
                        print("State Transition: IM_A->M @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!")
                elif (len(self.msgq_other) != 0) and (self.msgq_other[0]["type"] == "Inv-Ack") and (self.msgq_other[0]["dirblk"] == DirInd_dec):
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
                            print("State Transition: IM_A->M @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!")
          # State: S
            elif cache_line["protocol"] == "S":
                if op == "ld":
                    if (self.print_flag):
                        print("Cache Hit: Load @ $-line-" + str(index_dec) + ", addr-" + str(addr) + "!")
                elif op == "st":
                    # update output msg
                    self.msg_out = {
                        "type": "GetM",
                        "ack": 0,
                        "dirblk": DirInd_dec,
                        "src": "node_" + str(self.cache_ID),
                        "dst": "dir",
                        "req": "node_" + str(self.cache_ID)
                    }
                    self.msgq_out.append(self.msg_out)
                    # update cache line
                    self.cache_dict[str(index_dec)]["protocol"] = "SM_AD"
                    self.cache_dict[str(index_dec)]["addr"] = DirInd_dec
                    self.cache_dict[str(index_dec)]["tag"] = tag
                    self.cache_dict[str(index_dec)]["index"] = index_dec
                    self.cache_dict[str(index_dec)]["offset"] = None
                    if (self.print_flag): 
                        print("State Transition: S->SM_AD @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!")
                    # update CRHR
                    self.CRHR = True
                elif op == "ev":
                    # update output msg
                    self.msg_out = {
                        "type": "PutS",
                        "ack": 0,
                        "dirblk": DirInd_dec,
                        "src": "node_" + str(self.cache_ID),
                        "dst": "dir",
                        "req": None
                    }
                    self.msgq_out.append(self.msg_out)
                    # update cache line
                    self.cache_dict[str(index_dec)]["protocol"] = "SI_A"
                    if (self.print_flag): 
                        print("State Transition: S->SI_A @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!")
                    # update CRHR
                    self.CRHR = True
                elif (len(self.msgq_inv) != 0) and (self.msgq_inv[0]["dirblk"] == DirInd_dec):
                    # update output msg
                    self.msg_out = {
                        "type": "Inv-Ack",
                        "ack": 0,
                        "dirblk": DirInd_dec,
                        "src": "node_" + str(self.cache_ID),
                        "dst": self.msgq_inv[0]["req"],
                        "req": None
                    }
                    self.msgq_out.append(self.msg_out)
                    # Pop msg queue
                    self.msgq_inv.pop(0)
                    # update cache line
                    self.cache_dict[str(index_dec)]["protocol"] = "I"
                    self.cache_dict[str(index_dec)]["addr"] = None
                    self.cache_dict[str(index_dec)]["tag"] = None
                    self.cache_dict[str(index_dec)]["index"] = None
                    self.cache_dict[str(index_dec)]["offset"] = None
                    if (self.print_flag): 
                        print("State Transition: S->I @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!")
          # State: SM_AD
            elif cache_line["protocol"] == "SM_AD":
                if (len(self.msgq_inv) != 0) and (self.msgq_inv[0]["dirblk"] == DirInd_dec): # Check Inv first
                    # update output msg
                    self.msg_out = {
                        "type": "Inv-Ack",
                        "ack": 0,
                        "dirblk": DirInd_dec,
                        "src": "node_" + str(self.cache_ID),
                        "dst": self.msgq_inv[0]["req"],
                        "req": None
                    }
                    self.msgq_out.append(self.msg_out)
                    # Pop msg queue
                    self.msgq_inv.pop(0)
                    # update cache line
                    self.cache_dict[str(index_dec)]["protocol"] = "IM_AD"
                    if (self.print_flag): 
                        print("State Transition: SM_AD->IM_AD @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!")
                elif (len(self.msgq_other) != 0) and (self.msgq_other[0]["dirblk"] == DirInd_dec):
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
                            print("State Transition: SM_AD->M @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!")
                        # update CRHR
                        self.CRHR = False
                    elif (self.msgq_other[0]["type"] == "Data-FD" and self.msgq_other[0]["ack"] == 0):
                        # Pop msg queue
                        self.msgq_other.pop(0)
                        # update cache line
                        self.cache_dict[str(index_dec)]["protocol"] = "M"
                        if (self.print_flag):
                            print("State Transition: SM_AD->M @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!") 
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
                            print("State Transition: SM_AD->SM_A @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!")
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
                        print("State Transition: SM_A->M @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!")
                elif (len(self.msgq_other) != 0) and (self.msgq_other[0]["type"] == "Inv-Ack") and (self.msgq_other[0]["dirblk"] == DirInd_dec):
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
                            print("State Transition: SM_A->M @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!")
          # State: M
            elif cache_line["protocol"] == "M":
                if op == "ld":
                    if (self.print_flag):
                        print("Cache Hit: Load @ $-line-" + str(index_dec) + ", addr-" + str(addr) + "!")
                elif op == "st":
                    if (self.print_flag):
                        print("Cache Hit: Store @ $-line-" + str(index_dec) + ", addr-" + str(addr) + "!")
                elif op == "ev":
                    # update output msg
                    self.msg_out = {
                        "type": "PutM",
                        "ack": 0,
                        "dirblk": DirInd_dec,
                        "src": "node_" + str(self.cache_ID),
                        "dst": "dir",
                        "req": None
                    }
                    self.msgq_out.append(self.msg_out)
                    # update cache line
                    self.cache_dict[str(index_dec)]["protocol"] = "MI_A"
                    if (self.print_flag): 
                        print("State Transition: M->MI_A @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!")
                    # update CRHR
                    self.CRHR = True
                elif (len(self.msgq_fwd) != 0) and (self.msgq_fwd[0]["dirblk"] == DirInd_dec):
                    if (self.msgq_fwd[0]["type"] == "Fwd-GetS"):
                        # update output msg
                        self.msg_out = {
                            "type": "Data-FO",
                            "ack": 0,
                            "dirblk": DirInd_dec,
                            "src": "node_" + str(self.cache_ID),
                            "dst": self.msgq_fwd[0]["req"],
                            "req": None
                        }
                        self.msgq_out.append(self.msg_out)
                        self.msg_out = {
                            "type": "Data-TD",
                            "ack": 0,
                            "dirblk": DirInd_dec,
                            "src": "node_" + str(self.cache_ID),
                            "dst": "dir",
                            "req": None
                        }
                        self.msgq_out.append(self.msg_out)
                        # Pop msg queue
                        self.msgq_fwd.pop(0)
                        # update cache line
                        self.cache_dict[str(index_dec)]["protocol"] = "S"
                        if (self.print_flag): 
                            print("State Transition: M->S @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!")
                    elif (self.msgq_fwd[0]["type"] == "Fwd-GetM"):
                       # update output msg
                        self.msg_out = {
                            "type": "Data-FO",
                            "ack": 0,
                            "dirblk": DirInd_dec,
                            "src": "node_" + str(self.cache_ID),
                            "dst": self.msgq_fwd[0]["req"],
                            "req": None
                        }
                        self.msgq_out.append(self.msg_out)
                        # Pop msg queue
                        self.msgq_fwd.pop(0)
                        # update cache line
                        self.cache_dict[str(index_dec)]["protocol"] = "I"
                        self.cache_dict[str(index_dec)]["addr"] = None
                        self.cache_dict[str(index_dec)]["tag"] = None
                        self.cache_dict[str(index_dec)]["index"] = None
                        self.cache_dict[str(index_dec)]["offset"] = None
                        if (self.print_flag): 
                            print("State Transition: M->I @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!")
          # State: MI_A
            elif cache_line["protocol"] == "MI_A":
                if (len(self.msgq_fwd) != 0) and (self.msgq_fwd[0]["dirblk"] == DirInd_dec):
                    if (self.msgq_fwd[0]["type"] == "Fwd-GetS"):
                        # update output msg
                        self.msg_out = {
                            "type": "Data-FO",
                            "ack": 0,
                            "dirblk": DirInd_dec,
                            "src": "node_" + str(self.cache_ID),
                            "dst": self.msgq_fwd[0]["req"],
                            "req": None
                        }
                        self.msgq_out.append(self.msg_out)
                        self.msg_out = {
                            "type": "Data-TD",
                            "ack": 0,
                            "dirblk": DirInd_dec,
                            "src": "node_" + str(self.cache_ID),
                            "dst": "dir",
                            "req": None
                        }
                        self.msgq_out.append(self.msg_out)
                        # Pop msg queue
                        self.msgq_fwd.pop(0)
                        # update cache line
                        self.cache_dict[str(index_dec)]["protocol"] = "SI_A"
                        if (self.print_flag): 
                            print("State Transition: MI_A->SI_A @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!")
                    elif (self.msgq_fwd[0]["type"] == "Fwd-GetM"):
                       # update output msg
                        self.msg_out = {
                            "type": "Data-FO",
                            "ack": 0,
                            "dirblk": DirInd_dec,
                            "src": "node_" + str(self.cache_ID),
                            "dst": self.msgq_fwd[0]["req"],
                            "req": None
                        }
                        self.msgq_out.append(self.msg_out)
                        # Pop msg queue
                        self.msgq_fwd.pop(0)
                        # update cache line
                        self.cache_dict[str(index_dec)]["protocol"] = "II_A"
                        if (self.print_flag): 
                            print("State Transition: MI_A->II_A @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!")
                elif (len(self.msgq_other) != 0) and (self.msgq_other[0]["type"] == "Put-Ack") and (self.msgq_other[0]["dirblk"] == DirInd_dec):
                    # Pop msg queue
                    self.msgq_other.pop(0)
                    # update cache line
                    self.cache_dict[str(index_dec)]["protocol"] = "I"
                    self.cache_dict[str(index_dec)]["addr"] = None
                    self.cache_dict[str(index_dec)]["tag"] = None
                    self.cache_dict[str(index_dec)]["index"] = None
                    self.cache_dict[str(index_dec)]["offset"] = None
                    if (self.print_flag): 
                        print("State Transition: MI_A->I @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!")          
                    # update CRHR
                    self.CRHR = False
          # State: SI_A
            elif cache_line["protocol"] == "SI_A":
                if (len(self.msgq_inv) != 0) and (self.msgq_inv[0]["dirblk"] == DirInd_dec):
                    # update output msg
                    self.msg_out = {
                        "type": "Inv-Ack",
                        "ack": 0,
                        "dirblk": DirInd_dec,
                        "src": "node_" + str(self.cache_ID),
                        "dst": self.msgq_inv[0]["req"],
                        "req": None
                    }
                    self.msgq_out.append(self.msg_out)
                    # Pop msg queue
                    self.msgq_inv.pop(0)
                    # update cache line
                    self.cache_dict[str(index_dec)]["protocol"] = "II_A"
                    if (self.print_flag): 
                        print("State Transition: SI_A->II_A @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!")    
                elif (len(self.msgq_other) != 0) and (self.msgq_other[0]["type"] == "Put-Ack") and (self.msgq_other[0]["dirblk"] == DirInd_dec):
                    # Pop msg queue
                    self.msgq_other.pop(0)
                    # update cache line
                    self.cache_dict[str(index_dec)]["protocol"] = "I"
                    self.cache_dict[str(index_dec)]["addr"] = None
                    self.cache_dict[str(index_dec)]["tag"] = None
                    self.cache_dict[str(index_dec)]["index"] = None
                    self.cache_dict[str(index_dec)]["offset"] = None
                    if (self.print_flag): 
                        print("State Transition: SI_A->I @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!")          
                    # update CRHR
                    self.CRHR = False          
          # State: II_A
            elif cache_line["protocol"] == "II_A":
                if (len(self.msgq_other) != 0) and (self.msgq_other[0]["type"] == "Put-Ack") and (self.msgq_other[0]["dirblk"] == DirInd_dec):
                    # Pop msg queue
                    self.msgq_other.pop(0)
                    # update cache line
                    self.cache_dict[str(index_dec)]["protocol"] = "I"
                    self.cache_dict[str(index_dec)]["addr"] = None
                    self.cache_dict[str(index_dec)]["tag"] = None
                    self.cache_dict[str(index_dec)]["index"] = None
                    self.cache_dict[str(index_dec)]["offset"] = None
                    if (self.print_flag): 
                        print("State Transition: II_A->I @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!")          
                    # update CRHR
                    self.CRHR = False
             
      # Then handle incoming Fwd and Inv messages        
        if (len(self.msgq_inv) != 0):
            DirInd_dec = self.msgq_inv[0]["dirblk"]
            index_dec = DirInd_dec % self.cache_num_line
            cache_line = self.cache_dict[str(index_dec)]
          # State: S
            if cache_line["protocol"] == "S":
                # update output msg
                self.msg_out = {
                    "type": "Inv-Ack",
                    "ack": 0,
                    "dirblk": DirInd_dec,
                    "src": "node_" + str(self.cache_ID),
                    "dst": self.msgq_inv[0]["req"],
                    "req": None
                }
                self.msgq_out.append(self.msg_out)
                # Pop msg queue
                self.msgq_inv.pop(0)
                # update cache line
                self.cache_dict[str(index_dec)]["protocol"] = "I"
                self.cache_dict[str(index_dec)]["addr"] = None
                self.cache_dict[str(index_dec)]["tag"] = None
                self.cache_dict[str(index_dec)]["index"] = None
                self.cache_dict[str(index_dec)]["offset"] = None
                if (self.print_flag): 
                    print("State Transition: S->I @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!")
          # State: SM_AD
            elif cache_line["protocol"] == "SM_AD":
               # update output msg
                self.msg_out = {
                    "type": "Inv-Ack",
                    "ack": 0,
                    "dirblk": DirInd_dec,
                    "src": "node_" + str(self.cache_ID),
                    "dst": self.msgq_inv[0]["req"],
                    "req": None
                }
                self.msgq_out.append(self.msg_out)
                # Pop msg queue
                self.msgq_inv.pop(0)
                # update cache line
                self.cache_dict[str(index_dec)]["protocol"] = "IM_AD"
                self.cache_dict[str(index_dec)]["addr"] = None
                self.cache_dict[str(index_dec)]["tag"] = None
                self.cache_dict[str(index_dec)]["index"] = None
                self.cache_dict[str(index_dec)]["offset"] = None
                if (self.print_flag): 
                    print("State Transition: SM_AD->IM_AD @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!")            
          # State: SI_A  
            elif cache_line["protocol"] == "SI_A":
                # update output msg
                self.msg_out = {
                    "type": "Inv-Ack",
                    "ack": 0,
                    "dirblk": DirInd_dec,
                    "src": "node_" + str(self.cache_ID),
                    "dst": self.msgq_inv[0]["req"],
                    "req": None
                }
                self.msgq_out.append(self.msg_out)
                # Pop msg queue
                self.msgq_inv.pop(0)
                # update cache line
                self.cache_dict[str(index_dec)]["protocol"] = "II_A"
                self.cache_dict[str(index_dec)]["addr"] = None
                self.cache_dict[str(index_dec)]["tag"] = None
                self.cache_dict[str(index_dec)]["index"] = None
                self.cache_dict[str(index_dec)]["offset"] = None
                if (self.print_flag): 
                    print("State Transition: SI_A->II_A @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!")

        if (len(self.msgq_fwd) != 0):
            DirInd_dec = self.msgq_fwd[0]["dirblk"]
            index_dec = DirInd_dec % self.cache_num_line
            cache_line = self.cache_dict[str(index_dec)]
            if self.msgq_fwd[0]["type"] == "Fwd-GetS":
                if cache_line["protocol"] == "M":
                    # update output msg
                    self.msg_out = {
                        "type": "Data-FO",
                        "ack": 0,
                        "dirblk": DirInd_dec,
                        "src": "node_" + str(self.cache_ID),
                        "dst": self.msgq_fwd[0]["req"],
                        "req": None
                    }
                    self.msgq_out.append(self.msg_out)
                    self.msg_out = {
                        "type": "Data-TD",
                        "ack": 0,
                        "dirblk": DirInd_dec,
                        "src": "node_" + str(self.cache_ID),
                        "dst": "dir",
                        "req": None
                    }
                    self.msgq_out.append(self.msg_out)
                    # Pop msg queue
                    self.msgq_fwd.pop(0)
                    # update cache line
                    self.cache_dict[str(index_dec)]["protocol"] = "S"
                    if (self.print_flag): 
                        print("State Transition: M->S @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!")
                elif cache_line["protocol"] == "MI_A":
                    # update output msg
                    self.msg_out = {
                        "type": "Data-FO",
                        "ack": 0,
                        "dirblk": DirInd_dec,
                        "src": "node_" + str(self.cache_ID),
                        "dst": self.msgq_fwd[0]["req"],
                        "req": None
                    }
                    self.msgq_out.append(self.msg_out)
                    self.msg_out = {
                        "type": "Data-TD",
                        "ack": 0,
                        "dirblk": DirInd_dec,
                        "src": "node_" + str(self.cache_ID),
                        "dst": "dir",
                        "req": None
                    }
                    self.msgq_out.append(self.msg_out)
                    # Pop msg queue
                    self.msgq_fwd.pop(0)
                    # update cache line
                    self.cache_dict[str(index_dec)]["protocol"] = "SI_A"
                    if (self.print_flag): 
                        print("State Transition: MI_A->SI_A @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!")
            elif self.msgq_fwd[0]["type"] == "Fwd-GetM":
                if cache_line["protocol"] == "M":
                    # update output msg
                    self.msg_out = {
                        "type": "Data-FO",
                        "ack": 0,
                        "dirblk": DirInd_dec,
                        "src": "node_" + str(self.cache_ID),
                        "dst": self.msgq_fwd[0]["req"],
                        "req": None
                    }
                    self.msgq_out.append(self.msg_out)
                    # Pop msg queue
                    self.msgq_fwd.pop(0)
                    # update cache line
                    self.cache_dict[str(index_dec)]["protocol"] = "I"
                    self.cache_dict[str(index_dec)]["addr"] = None
                    self.cache_dict[str(index_dec)]["tag"] = None
                    self.cache_dict[str(index_dec)]["index"] = None
                    self.cache_dict[str(index_dec)]["offset"] = None
                    if (self.print_flag): 
                        print("State Transition: M->I @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!")
                elif cache_line["protocol"] == "MI_A":
                    # update output msg
                    self.msg_out = {
                        "type": "Data-FO",
                        "ack": 0,
                        "dirblk": DirInd_dec,
                        "src": "node_" + str(self.cache_ID),
                        "dst": self.msgq_fwd[0]["req"],
                        "req": None
                    }
                    self.msgq_out.append(self.msg_out)
                    # Pop msg queue
                    self.msgq_fwd.pop(0)
                    # update cache line
                    self.cache_dict[str(index_dec)]["protocol"] = "II_A"
                    if (self.print_flag): 
                        print("State Transition: MI_A->II_A @ $-line-" + str(index_dec) + ", dir-block-" + str(DirInd_dec) + "!")
        
    # MESI cache coherence protocol controller
    def dir_ctrl_mesi(self):
        pass
    
    # MOSI cache coherence protocol controller
    def dir_ctrl_mosi(self):
        pass