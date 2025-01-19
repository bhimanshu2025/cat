from collections import OrderedDict
from flask import current_app
from datetime import datetime, timedelta

class CatCache(object):
    def __init__(self, name, max_size=1000, max_flush=10, flush_at_size=990, refresh_time=1):
        self._cached_dict = OrderedDict()
        self._name = name
        self._max_size = max_size
        self._max_flush = max_flush
        self._flush_at_size = flush_at_size
        self.refresh_time = refresh_time
        current_app.logger.info(f'Cache Initialized: {self._name}')

    def __repr__(self):
        return f"CatCache'{self._name}', '{self.__current_size()}''"
    
    def add(self, ke, va):
        self.__flush()
        self._cached_dict[ke] = [datetime.now(), va]
        current_app.logger.debug(f'Added an item to local cache {self._name}: {ke}')
        current_app.logger.debug(f'local cache {self._name} size: {self.__current_size()}')
        
    def __current_size(self):
        return len(self._cached_dict)
    
    def __flush(self):
        if self._flush_at_size <= self.__current_size():
            for i in range(self._max_flush):
                last_item = self._cached_dict.popitem(last=True)
                current_app.logger.debug(f'Removed an item from local cache {self._name}: {last_item}')
        
    def search(self, ke):
        if self._cached_dict.get(ke) and not self._check_if_expired(self._cached_dict.get(ke)[0]):
            current_app.logger.debug(f'Local cache hit {self._name}: {ke}')
            return self._cached_dict.get(ke)[1]
        else:
            current_app.logger.debug(f'Local cache miss {self._name}: {ke}')
            return None

    # check if the entry needs to be refreshed from Salesforce
    def _check_if_expired(self, dt):
        if datetime.now() - timedelta(minutes=self.refresh_time) > dt:
            current_app.logger.debug(f'Local cache hit but expired {self._name}')
            return True
        else:
            return False


