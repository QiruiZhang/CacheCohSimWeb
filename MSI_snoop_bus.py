class bus():
    def __init__(self):
        self.all_caches = []

    def add_cache(self, cache):
        self.all_caches.append(cache)

    def BusInv(self, cache_id, addr):
        Reply = None
        BusReply_Fin = None
        for cache in self.all_caches:
            valid = False
            if cache.cache_ID != cache_id:
                valid, Reply = cache.handle_BusInv(addr)
            if valid == True:
                BusReply_Fin = Reply
        return BusReply_Fin

    def BusRd(self, cache_id, addr):
        Reply = None
        BusReply_Fin = None
        mem = False
        mem_addr = None
        for cache in self.all_caches:
            valid = False
            if cache.cache_ID != cache_id:
                valid, Reply, mem, mem_addr = cache.handle_BusRd(addr)
            if valid == True:
                BusReply_Fin = Reply
        return BusReply_Fin, mem, mem_addr

    def BusRdX(self, cache_id, addr):
        Reply = None
        BusReply_Fin = None
        for cache in self.all_caches:
            valid = False
            if cache.cache_ID != cache_id:
                #print(f"cache_ID is {cache.cache_ID} and cache_id is {cache_id}")
                valid, Reply = cache.handle_BusRdX(addr)
            if valid == True:
                BusReply_Fin = Reply
        return BusReply_Fin
