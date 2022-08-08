import gc


class Memory:
    def __init__(self, logger):
        self.log = logger

    def clean_ram(self):
        self.log.debug('Clean RAM Memory')
        mem_alloc = gc.mem_alloc()/1000
        mem_size = (gc.mem_alloc() + gc.mem_free())/1000
        mem_usage_percent = (mem_alloc/mem_size)*100
        self.log.debug('RAM usage before cleanup: {} KB / {} KB  ({} %)'.format(mem_alloc, mem_size, mem_usage_percent))
        gc.collect()
        mem_alloc = gc.mem_alloc()/1000
        mem_size = (gc.mem_alloc() + gc.mem_free())/1000
        mem_usage_percent = (mem_alloc/mem_size)*100
        self.log.debug('RAM usage after cleanup: {} KB / {} KB  ({} %)'.format(mem_alloc, mem_size, mem_usage_percent))

    def show_ram_usage(self):
        mem_alloc = gc.mem_alloc()/1000
        mem_size = (gc.mem_alloc() + gc.mem_free())/1000
        mem_usage_percent = (mem_alloc/mem_size)*100
        self.log.debug('RAM usage: {} KB / {} KB  ({} %)'.format(mem_alloc, mem_size, mem_usage_percent))