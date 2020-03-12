from collections import OrderedDict
from socket import *
from threading import Thread
from struct import pack,unpack,calcsize
from time import sleep,time

#-------------------------------------------------------------------------
# DnsRecord
#-------------------------------------------------------------------------
class DnsRecord:

    # ============================================
    # ============================================
    def __init__( self, name, rtype, value, ttl, static ):
        self.name = name
        self.type = rtype
        self.value = value
        self.ttl = ttl
        self.static = static


#-------------------------------------------------------------------------
# DnsMessage
#------------------------------------------------------------------------- 
class DnsMessage:

    types = {   
                'A':     '1000',
                'AAAA':  '0100',
                'CNAME': '0010',
                'NS':    '0001'
            }

    # ============================================
    # ============================================
    def __init__( self, tid, is_response, rtype, name, value ):
        self.tid = tid
        self.is_response = is_response
        self.type = rtype
        self.name = name
        self.value = value

    # ============================================
    # ============================================
    def encode( self ):
        fmt = '!IBII'+str(len(self.name))+'s'+str(len(self.value))+'s'
        rtype = DnsMessage.types[self.type] 
        qr = format( self.is_response, '#04' )
        qr_type = int( '0b'+qr+rtype, 2 )
        encMsg = pack( fmt, self.tid, qr_type, len(self.name), len(self.value), self.name.encode(), self.value.encode() )
        return encMsg

    # ============================================
    # ============================================
    @staticmethod
    def decode_message( encMsg ):
        nlength = int(str(encMsg[5])+str(encMsg[6])+str(encMsg[7])+str(encMsg[8]))
        vlength = int(str(encMsg[9])+str(encMsg[10])+str(encMsg[11])+str(encMsg[12]))
        fmt = '!IBII'+str(nlength)+'s'+str(vlength)+'s'
        if len( encMsg ) != calcsize( fmt ):
            return None
        
        decMsg = unpack( fmt, encMsg )
        qr_type = format( decMsg[1], '#010b' )


        tid = decMsg[0]
        qr = bool( int(qr_type[2:6]) )
        rtype = None
        for key in DnsMessage.types:
            if DnsMessage.types[key] == qr_type[6:]:
                rtype = key
        name = decMsg[4].decode()
        value = decMsg[5].decode()

        return DnsMessage( tid, qr, rtype, name, value )


#-------------------------------------------------------------------------
# DnsTable
#-------------------------------------------------------------------------
class DnsTable:

    # ============================================
    # ============================================
    def __init__( self ):
        self.rr = OrderedDict()

        # Start a separate thread to manage TTL times
        # and delete expired entries
        #
        self._stop_threads = False
        self._ttl_tick_thread = Thread( target = self._tick_ttl ) 
        self._ttl_tick_thread.start()

    # ============================================
    # ============================================
    def _tick_ttl( self ):
        # Delete any records that have outlived their TTL
        #
        while True:
            if self._stop_threads:
                break

            sleep( 1 )
            for key in self.rr:
                self._ttls_locked = True
                self.rr[key].ttl -= 1
                if self.rr[key].static == 0 and self.rr[key].ttl <= 0:
                    del self.rr[key]
                self._ttls_locked = False

    # ============================================
    # ============================================
    def destroy( self ):
        self._stop_threads = True
        del self

    # ============================================
    # ============================================
    def touch_record( self, record ):
        key = record.name+':'+record.type
        if key not in self.rr.keys():
            self.rr[key] = record 
        else:
            if self.rr[key].static == 0:
                self.rr[key].ttl = 60

            
#-------------------------------------------------------------------------
# DnsServer 
#-------------------------------------------------------------------------
class DnsServer:

    # ============================================
    # ============================================
    def __init__( self, name, port ):
        self._pending_queries = {}
        self._tid = 0
        self.name = name
        self.port = port
        self.dns_table = DnsTable()
        self._socket = socket( AF_INET, SOCK_DGRAM )

        self._socket.bind( ('127.0.0.1', self.port) )
        print( self.name+' listening on port '+str(self.port)+'...' )
    
    # ============================================
    # ============================================
    def handle_dns_message( self ):
        enc_msg, src_address = self._socket.recvfrom( 2048 )
        src_msg = DnsMessage.decode_message( enc_msg )

        # If the message received is in the wrong format, it
        # will decode as None. Throw an error to the sender
        #
        if src_msg is None:
            value = 'Invalid query!'
            err_msg = DnsMessage( src_msg.tid, True, src_msg.type, src_msg.name, value )  
            print( str(time())+' '+self.name+': Invalid query received.' )
            self._socket.sendto( err_msg.encode(), src_address )
            return

        if src_msg.is_response:
            self._handle_response( src_msg, src_address )
        else:
            self._handle_query( src_msg, src_address )

    # ============================================
    # ============================================
    def _handle_query( self, src_msg, src_address ):
        ret_msg = None
        key = src_msg.name+':'+src_msg.type
        print( 'LOOKING FOR '+key )

        # If the the local record table has what we're looking for
        # prepare a message with that information
        #
        if key in self.dns_table.rr.keys():
            dns_rec = self.dns_table.rr[key]
            ret_msg = DnsMessage( src_msg.tid, True, dns_rec.type, dns_rec.name, dns_rec.value ) 
            print( str(time())+' '+self.name+': Found record in local table.' )

        # If not, look for an authoritative server in local records
        #
        else:
            # If authoritative server is found, send it a query,
            # and return that response to sender
            #
            domain = src_msg.name.split( '.', 1 )[1]
            domain_key = domain+':NS'
            if domain_key in self.dns_table.rr.keys():
                auth_port = None
                if domain == 'qualcomm.com':
                    auth_port = 21000
                elif domain == 'viasat.com':
                    auth_port = 22000
                auth_msg = DnsMessage( self._generate_tid(), False, 'A', src_msg.name, '' )
                self._pending_queries[self._tid] = (src_address, src_msg.tid)

                print( str(time())+' '+self.name+': Found authoritative server in local table. Sending request to port '+str(auth_port)+'...' )
                self._socket.sendto( auth_msg.encode(), ('127.0.0.1', auth_port) )
                return
                
            # If not found, let the sender know
            #
            else:
                value = 'No DNS record found for '+src_msg.name
                ret_msg = DnsMessage( src_msg.tid, src_msg.is_response, src_msg.type, src_msg.name, value )
                print( str(time())+' '+self.name+': No record found for '+src_msg.name )

        # Send final response back to client 
        #
        print( str(time())+' '+self.name+': Sending response to '+str(src_address)+' from _handle_query: '+ret_msg.value )
        self._socket.sendto( ret_msg.encode(), src_address )

    # ============================================
    # ============================================
    def _handle_response( self, auth_msg, src_address ):
        print( str(time())+' '+self.name+': Received response from '+str(src_address)+': '+auth_msg.value )
        client_address,client_tid = self._pending_queries[auth_msg.tid]
        del self._pending_queries[auth_msg.tid]
        auth_msg.tid = client_tid
        print( str(time())+' '+self.name+': Sending response to '+str(client_address)+' from _handle_reponse: '+auth_msg.value )
        self._socket.sendto( auth_msg.encode(), client_address )
        self.dns_table.touch_record( DnsRecord(auth_msg.name, auth_msg.type, auth_msg.value, 60, 0) )

    # ============================================
    # ============================================
    def _generate_tid( self ):
        self._tid += 1
        return self._tid
