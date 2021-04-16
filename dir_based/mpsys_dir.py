# -*- coding: utf-8 -*-
import dir_node as dn
import proc_node as pn

class mpsys_dir():
    def __init__(self, inst_dict, print_flag = True):
        self.protocol = inst_dict["protocol"]
        self.num_proc = inst_dict["num_cache"]
        self.line_size = inst_dict["line_size"]
        self.cache_size = inst_dict["cache_size"]
        self.mem_size = inst_dict["mem_size"]

        self.cache_type = inst_dict["cache_type"]
        self.cache_way = inst_dict["cache_way"]

        self.print_flag = print_flag

        # Initialize Nodes
        self.dir_node = dn.dir_node(self.protocol, self.line_size, self.mem_size, self.print_flag)
        self.proc_nodes = []
        for i in range(0, self.num_proc):
            self.proc_nodes.append( \
                pn.proc_node(i, inst_dict["node_"+str(i)], self.protocol, self.cache_size, self.line_size, self.mem_size, [], self.print_flag) \
            )

        self.msg_log = []

    # Reset PCs and dicts to default values
    def reset(self):
        # Reset Directory Node
        self.dir_node.dir_reset()

        # Reset Processor Node
        for i in range(0, self.num_proc):
            self.proc_nodes[i].proc_reset()

    # Update Nodes with input dicts from cache.json
    def update_dict(self, cache_dict):
        # Update Directory Dict
        self.dir_node.dir_dict = cache_dict["dir"]["dict"]

        # Update Processor Dicts
        for i in range(0, self.num_proc):
            self.proc_nodes[i].cache_dict = cache_dict[str(i)]["cache"]
    
    # Output data into cache.json
    def output_dict(self):
        cache_dict = {}
        # Add Processor Node Data
        for i in range(0, self.num_proc):
            cache_dict[str(i)] = self.proc_nodes[i].return_cache_dict()[str(i)]
            cache_dict[str(i)]["PC"] = self.proc_nodes[i].PC
            cache_dict[str(i)]["log"] = self.proc_nodes[i].node_log

        # Add Directory Data
        cache_dict["dir"] = {}
        cache_dict["dir"]["dict"] = self.dir_node.return_dir_dict()["dir"]
        cache_dict["dir"]["log"] = self.dir_node.dir_log

        # Add Interconnect Message log
        cache_dict["msg"] = self.msg_log

        return cache_dict

    def send_msg(self, msg):
        if msg["dst"] == "dir":
            self.dir_node.input_msg(msg)
        else:
            self.proc_nodes[int(msg["dst"][5:])].input_msg(msg)

        log = "Message Transaction: " + msg["src"] + " sent " + msg["type"]
        if msg["type"] == "Data-FD":
            log += " (ack = " + str(msg["ack"]) + ")" 
        log += " to " + msg["dst"] + " for dir-block-" + str(msg["dirblk"])
        if msg["req"] != None:
            log += " requested by " + msg["req"]

        self.msg_log.append(log)
        if (self.print_flag):
            print(log)

    # Toggle Clock of Multi-Processor System by one cycle
    def run_cycle(self, proc_sel):
        '''
        Run Processors
        proc_sel:
            "all": run all processors concurrently
            "0" ~ str(num_proc-1): run only self.proc_nodes[int(proc_sel)] 
        '''
        if proc_sel == "all":
            for i in range(0, self.num_proc):
                self.proc_nodes[i].proc_run()
        else:
            self.proc_nodes[int(proc_sel)].proc_run()

        # Run Directory
        self.dir_node.dir_run()

        # Message Transactions
        self.msg_log = []
        for i in range(0, self.num_proc):
            for j in range(0, len(self.proc_nodes[i].msgq_out)):
                msg = self.proc_nodes[i].output_msg()
                self.send_msg(msg)
        
        for i in range(0, len(self.dir_node.msgq_out)):
            msg = self.dir_node.output_msg()
            self.send_msg(msg)


    
        