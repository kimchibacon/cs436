from collections import OrderedDict
import threading
from time import sleep

class DnsRecord:
    def __init__( self, name, rtype, value, ttl, static ):
        self.name = name
        self.type = rtype
        self.value = value
        self.ttl = ttl
        self.static = static

class DnsMessage:
    def __init__( self, tid, qr, rtype, nlength, vlength, name, value ):
        self.tid = tid
        self.qr = qr
        self.type = rtype
        self.name_length = nlength
        self.vlength = value_length
        self.name = name
        self.value = value

class DnsTable:
    def __init__( self ):
        # Private Ordered Dict to hold DnsMessages
        #
        self._rr = OrderedDict()
        
        # Start a separate thread to manage TTL times
        #
        self._ttlTickThread = threading.Thread( target = self._tickTTL ) 
        self._ttlTickThread.start()
    
    def __getitem__( self, key ):
        return self._rr[key]

    def __setitem__( self, key, value ):
        self._rr[key] = value

    def _tickTTL( self ):
        # Delete any records that have outlived their TTL
        #
        while True:
            sleep( 1 )
            for key in self._rr:
                self._rr[key].ttl -= 1
                if self._rr[key].static == 0 and self._rr[key].ttl <= 0:
                    del self._rr[key]
