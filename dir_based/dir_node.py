# -*- coding: utf-8 -*-
import math

# Directory Node Class
class dir_node():
    def __init__(self, protocol = 'MSI', line_size = 8, mem_size = 512, print_flag = True):
        self.protocol = protocol # Protocol type: MSI, MESI or MOSI

        self.mem_size = mem_size # Bytes
        self.mem_line_size = line_size #Bytes
        self.dir_dict = {}
        self.dir_num_line = int(self.mem_size/self.mem_line_size)

        for i in range(self.dir_num_line):
            self.dir_dict[str(i)] = {
                "addr": None, # directory block index, decimal
                "protocol": "I",
                "owner": None,
                "sharers": [],
                "ack_needed": 0,
                "ack_cnt": 0
            }


        self.print_flag = print_flag

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
                Fwd-Ack
                
            node<->node message types:
                Data-FO (Data from Owner)
                Inv-Ack
        '''
        self.dir_log = []

    def dir_reset(self):
        # Reset dict
        for i in range(self.dir_num_line):
            self.dir_dict[str(i)] = {
                "addr": None, # directory block index, decimal
                "protocol": "I",
                "owner": None,
                "sharers": [],
                "ack_needed": 0,
                "ack_cnt": 0
            }

        # Reset Queues
        self.msgq_req = []
        self.msgq_resp = []
        self.msgq_out = []

        # Reset log
        self.dir_log = []

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
        if msg['type'] == 'Data-TD' or msg['type'] == 'Fwd-Ack' or msg['type'] == 'Inv-Ack':
            self.msgq_resp.append(msg)
        else:
            self.msgq_req.append(msg)
    
    # Get message output of the current cycle
    def output_msg(self):
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
        msgq_req_popped = False
        self.dir_log = []

      # Process msgq_req
        if (len(self.msgq_req) != 0):
            head_msg = self.msgq_req[0]
            dir_line = self.dir_dict[str(head_msg["dirblk"])]
            if (dir_line["protocol"] == "I"):
                if (head_msg["type"] == "GetS"):
                    # Update output message
                    self.msg_out = {
                        "type": "Data-FD",
                        "ack": 0,
                        "dirblk": head_msg["dirblk"],
                        "src": "dir",
                        "dst": head_msg["src"],
                        "req": None
                    }
                    self.msgq_out.append(self.msg_out)
                    
                    # Update Directory State
                    dir_line["addr"] = head_msg["dirblk"]
                    dir_line["sharers"].append(head_msg["src"])
                    dir_line["protocol"] = "S"
                    
                    # Update log
                    log = "Directory State Transition: I->S @ dir-block-" + str(head_msg["dirblk"]) + "!"
                    self.dir_log.append(log)
                    if self.print_flag:
                        print(log)
                    
                    # Pop input queue
                    self.msgq_req.pop(0)
                    msgq_req_popped = True
                elif (head_msg["type"] == "GetM"):
                    # Update output message
                    self.msg_out = {
                        "type": "Data-FD",
                        "ack": 0,
                        "dirblk": head_msg["dirblk"],
                        "src": "dir",
                        "dst": head_msg["src"],
                        "req": None
                    }
                    self.msgq_out.append(self.msg_out)
                    
                    # Update Directory State
                    dir_line["addr"] = head_msg["dirblk"]
                    dir_line["owner"] = head_msg["src"]
                    dir_line["protocol"] = "M"

                    # Update log
                    log = "Directory State Transition: I->M @ dir-block-" + str(head_msg["dirblk"]) + "!"
                    self.dir_log.append(log)
                    if self.print_flag:
                        print(log)

                    # Pop input queue
                    self.msgq_req.pop(0)
                    msgq_req_popped = True
                elif (head_msg["type"] == "PutS"):
                    # Update output message
                    self.msg_out = {
                        "type": "Put-Ack",
                        "ack": 0,
                        "dirblk": head_msg["dirblk"],
                        "src": "dir",
                        "dst": head_msg["src"],
                        "req": None
                    }
                    self.msgq_out.append(self.msg_out)

                    # Pop input queue
                    self.msgq_req.pop(0)
                    msgq_req_popped = True
                elif (head_msg["type"] == "PutM"):
                    # Update output message
                    self.msg_out = {
                        "type": "Put-Ack",
                        "ack": 0,
                        "dirblk": head_msg["dirblk"],
                        "src": "dir",
                        "dst": head_msg["src"],
                        "req": None
                    }
                    self.msgq_out.append(self.msg_out)

                    # Pop input queue
                    self.msgq_req.pop(0)
                    msgq_req_popped = True
                else:
                    pass
            elif (dir_line["protocol"] == "S"):
                scnt = len(dir_line["sharers"])
                scnt_deduct = int(head_msg["src"] in dir_line["sharers"])
                if (head_msg["type"] == "GetS"):
                    # Update output message
                    self.msg_out = {
                        "type": "Data-FD",
                        "ack": 0,
                        "dirblk": head_msg["dirblk"],
                        "src": "dir",
                        "dst": head_msg["src"],
                        "req": None
                    }
                    self.msgq_out.append(self.msg_out)
                    
                    # Update Directory State
                    dir_line["sharers"].append(head_msg["src"])

                    # Pop input queue
                    self.msgq_req.pop(0)
                    msgq_req_popped = True
                elif (head_msg["type"] == "GetM"):
                    # Update output message
                    self.msg_out = {
                        "type": "Data-FD",
                        "ack": scnt - scnt_deduct,
                        "dirblk": head_msg["dirblk"],
                        "src": "dir",
                        "dst": head_msg["src"],
                        "req": None
                    }
                    self.msgq_out.append(self.msg_out)
                    
                    # Send Inv to sharers
                    for dst in dir_line["sharers"]:
                        if (dst != head_msg["src"]):
                            self.msg_out = {
                                "type": "Inv",
                                "ack": 0,
                                "dirblk": head_msg["dirblk"],
                                "src": "dir",
                                "dst": dst,
                                "req": head_msg["src"]
                            }
                            self.msgq_out.append(self.msg_out)

                    # Update Directory State
                    if ((scnt == 1) and (head_msg["src"] in dir_line["sharers"])):
                        dir_line["sharers"] = []
                        dir_line["owner"] = head_msg["src"]
                        dir_line["protocol"] = "M"
                        
                        # Update log
                        log = "Directory State Transition: S->M @ dir-block-" + str(head_msg["dirblk"]) + "!"
                        self.dir_log.append(log)
                        if self.print_flag:
                            print(log)
                    else:
                        dir_line["sharers"] = []
                        dir_line["owner"] = head_msg["src"]
                        dir_line["ack_needed"] = scnt - scnt_deduct
                        dir_line["ack_cnt"] = 0
                        dir_line["protocol"] = "SM_A"
                        
                        # Update log
                        log = "Directory State Transition: S->SM_A @ dir-block-" + str(head_msg["dirblk"]) + "!"
                        self.dir_log.append(log)
                        if self.print_flag:
                            print(log)

                    # Pop input queue
                    self.msgq_req.pop(0)
                    msgq_req_popped = True
                elif (head_msg["type"] == "PutS"):
                    # Update output message
                    self.msg_out = {
                        "type": "Put-Ack",
                        "ack": 0,
                        "dirblk": head_msg["dirblk"],
                        "src": "dir",
                        "dst": head_msg["src"],
                        "req": None
                    }
                    self.msgq_out.append(self.msg_out)

                    # Update Directory State
                    if ((scnt == 1) and (head_msg["src"] in dir_line["sharers"])):
                        dir_line["sharers"].remove(head_msg["src"])
                        dir_line["protocol"] = "I"
                        dir_line["addr"] = None

                        # Update log
                        log = "Directory State Transition: S->I @ dir-block-" + str(head_msg["dirblk"]) + "!"
                        self.dir_log.append(log)
                        if self.print_flag:
                            print(log)
                    else:
                        dir_line["sharers"].remove(head_msg["src"])

                    # Pop input queue
                    self.msgq_req.pop(0)
                    msgq_req_popped = True
                elif (head_msg["type"] == "PutM"):
                    # Update output message
                    self.msg_out = {
                        "type": "Put-Ack",
                        "ack": 0,
                        "dirblk": head_msg["dirblk"],
                        "src": "dir",
                        "dst": head_msg["src"],
                        "req": None
                    }
                    self.msgq_out.append(self.msg_out)

                    # Update Directory State
                    if ((scnt == 1) and (head_msg["src"] in dir_line["sharers"])):
                        dir_line["sharers"].remove(head_msg["src"])
                        dir_line["protocol"] = "I"
                        dir_line["addr"] = None

                        # Update log
                        log = "Directory State Transition: S->I @ dir-block-" + str(head_msg["dirblk"]) + "!"
                        self.dir_log.append(log)
                        if self.print_flag:
                            print(log)
                    else:
                        dir_line["sharers"].remove(head_msg["src"])

                    # Pop input queue
                    self.msgq_req.pop(0)
                    msgq_req_popped = True
                else:
                    pass            
            elif (dir_line["protocol"] == "SM_A"):
                pass
            elif (dir_line["protocol"] == "M"):
                if (head_msg["type"] == "GetS"):
                    # Update output message
                    self.msg_out = {
                        "type": "Fwd-GetS",
                        "ack": 0,
                        "dirblk": head_msg["dirblk"],
                        "src": "dir",
                        "dst": dir_line["owner"],
                        "req": head_msg["src"]
                    }
                    self.msgq_out.append(self.msg_out)
                    
                    # Update Directory State
                    dir_line["sharers"].append(head_msg["src"])
                    dir_line["sharers"].append(dir_line["owner"])
                    dir_line["owner"] = None
                    dir_line["protocol"] = "MS_D"
                    
                    # Update log
                    log = "Directory State Transition: M->MS_D @ dir-block-" + str(head_msg["dirblk"]) + "!"
                    self.dir_log.append(log)
                    if self.print_flag:
                        print(log)
                    
                    # Pop input queue
                    self.msgq_req.pop(0)
                    msgq_req_popped = True
                elif (head_msg["type"] == "GetM"):
                    # Update output message
                    self.msg_out = {
                        "type": "Fwd-GetM",
                        "ack": 0,
                        "dirblk": head_msg["dirblk"],
                        "src": "dir",
                        "dst": dir_line["owner"],
                        "req": head_msg["src"]
                    }
                    self.msgq_out.append(self.msg_out)
                    
                    # Update Directory State
                    dir_line["owner"] = head_msg["src"]
                    dir_line["protocol"] = "MM_A"

                    # Update log
                    log = "Directory State Transition: M->MM_A @ dir-block-" + str(head_msg["dirblk"]) + "!"
                    self.dir_log.append(log)
                    if self.print_flag:
                        print(log)

                    # Pop input queue
                    self.msgq_req.pop(0)
                    msgq_req_popped = True
                elif (head_msg["type"] == "PutS"):
                    # Update output message
                    self.msg_out = {
                        "type": "Put-Ack",
                        "ack": 0,
                        "dirblk": head_msg["dirblk"],
                        "src": "dir",
                        "dst": head_msg["src"],
                        "req": None
                    }
                    self.msgq_out.append(self.msg_out)

                    # Pop input queue
                    self.msgq_req.pop(0)
                    msgq_req_popped = True
                elif (head_msg["type"] == "PutM"):
                    # Update output message
                    self.msg_out = {
                        "type": "Put-Ack",
                        "ack": 0,
                        "dirblk": head_msg["dirblk"],
                        "src": "dir",
                        "dst": head_msg["src"],
                        "req": None
                    }
                    self.msgq_out.append(self.msg_out)

                    # Update Directory State
                    if (head_msg["src"] == dir_line["owner"]):
                        dir_line["owner"] = None
                        dir_line["protocol"] = "I"
                        dir_line["addr"] = None

                        # Update log
                        log = "Directory State Transition: M->I @ dir-block-" + str(head_msg["dirblk"]) + "!"
                        self.dir_log.append(log)
                        if self.print_flag:
                            print(log)

                    # Pop input queue
                    self.msgq_req.pop(0)
                    msgq_req_popped = True
                else:
                    pass            
            elif (dir_line["protocol"] == "MM_A"):
                if (head_msg["type"] == "PutS"):
                    # Update output message
                    self.msg_out = {
                        "type": "Put-Ack",
                        "ack": 0,
                        "dirblk": head_msg["dirblk"],
                        "src": "dir",
                        "dst": head_msg["src"],
                        "req": None
                    }
                    self.msgq_out.append(self.msg_out)

                    # Pop input queue
                    self.msgq_req.pop(0)
                    msgq_req_popped = True
                else:
                    pass
            elif (dir_line["protocol"] == "MS_D"):
                pass
            else:
                pass
        
      # Process msgq_resp
        if ((len(self.msgq_resp) != 0) and (not msgq_req_popped)):
            head_msg = self.msgq_resp[0]
            dir_line = self.dir_dict[str(head_msg["dirblk"])]
            if (dir_line["protocol"] == "I"):
                pass
            elif (dir_line["protocol"] == "S"):
                pass
            elif (dir_line["protocol"] == "SM_A"):
                if (head_msg["type"] == "Inv-Ack"):
                    dir_line["ack_cnt"] += 1
                    if (dir_line["ack_cnt"] == dir_line["ack_needed"]):
                        dir_line["ack_cnt"] = 0
                        dir_line["ack_needed"] = 0
                        dir_line["protocol"] = "M"
                        
                        # Update log
                        log = "Directory State Transition: SM_A->M @ dir-block-" + str(head_msg["dirblk"]) + "!"
                        self.dir_log.append(log)
                        if self.print_flag:
                            print(log)
                
                    # Pop input queue
                    self.msgq_resp.pop(0)
                else:
                    pass
            elif (dir_line["protocol"] == "M"):
                pass
            elif (dir_line["protocol"] == "MM_A"):
                if (head_msg["type"] == "Fwd-Ack"):
                    # Update Directory State
                    dir_line["protocol"] = "M"

                    # Update log
                    log = "Directory State Transition: MM_A->M @ dir-block-" + str(head_msg["dirblk"]) + "!"
                    self.dir_log.append(log)
                    if self.print_flag:
                        print(log)

                    # Pop input queue
                    self.msgq_resp.pop(0)
                else:
                    pass
            elif (dir_line["protocol"] == "MS_D"):
                if (head_msg["type"] == "Data-TD"):
                    # Update Directory State
                    dir_line["protocol"] = "S"

                    # Update log
                    log = "Directory State Transition: MS_D->S @ dir-block-" + str(head_msg["dirblk"]) + "!"
                    self.dir_log.append(log)
                    if self.print_flag:
                        print(log)

                    # Pop input queue
                    self.msgq_resp.pop(0)
                else:
                    pass            
            else:
                pass
            
    # MESI cache coherence protocol controller
    def dir_ctrl_mesi(self):
        pass
    
    # MOSI cache coherence protocol controller
    def dir_ctrl_mosi(self):
        pass