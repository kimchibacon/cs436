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
                'A':        '1000',
                'AAAA':     '0100',
                'CNAME':    '0010',
                'NS':       '0001',
                'INVALID':  '0000'
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
        
        rtype = None
        if self.type in DnsMessage.types.keys():
            rtype = DnsMessage.types[self.type]
        else:
            rtype = DnsMessage.types['INVALID']

        qr = format( self.is_response, '#04' )
        qr_type = int( '0b'+qr+rtype, 2 )
        encMsg = pack( fmt, self.tid, qr_type, len(self.name), len(self.value), self.name.encode(), self.value.encode() )
        return encMsg

    # ============================================
    # ============================================
    @staticmethod
    def decode_message( encMsg ):
        message_valid = True

        nlength = int(str(encMsg[5])+str(encMsg[6])+str(encMsg[7])+str(encMsg[8]))
        vlength = int(str(encMsg[9])+str(encMsg[10])+str(encMsg[11])+str(encMsg[12]))
        fmt = '!IBII'+str(nlength)+'s'+str(vlength)+'s'
        if len( encMsg ) != calcsize( fmt ):
            message_valid = False
        
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

        if rtype is None or rtype == 'INVALID' or '.' not in name:
            message_valid = False
        
        if message_valid:
            return DnsMessage( tid, qr, rtype, name, value )
        else:
            return DnsMessage( 0, False, 'INVALID', 'INVALID', 'Invalid format' )


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
            expired_records = [] 
            self._ttls_locked = True

            for key in self.rr:
                self.rr[key].ttl -= 1
                if self.rr[key].static == 0 and self.rr[key].ttl <= 0:
                    expired_records.append( key )

            for key in expired_records:
                del self.rr[key]    
                
            self._ttls_locked = False

    # ============================================
    # ============================================
    def destroy( self ):
        self._stop_threads = True
        del self

    # ============================================
    # ============================================
    def append_record( self, record ):
        key = record.name+':'+record.type
        if key not in self.rr.keys():
            self.rr[key] = record 

            
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
        if src_msg.type == 'INVALID':
            value = 'Invalid query!'
            print( str(time())+' '+self.name+': Invalid message received.' )
            self._socket.sendto( src_msg.encode(), src_address )
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

        print( str(time())+' '+self.name+': Request received from host at '+src_address[0]+':'+str(src_address[1])+' for hostname "'+src_msg.name+'"' )

        # If the the local record table has what we're looking for
        # prepare a message with that information
        #
        if key in self.dns_table.rr.keys():
            dns_rec = self.dns_table.rr[key]
            ret_msg = DnsMessage( src_msg.tid, True, dns_rec.type, dns_rec.name, dns_rec.value ) 
            print( str(time())+' '+self.name+': Found "'+src_msg.type+'" record for "'+src_msg.name+'" in local table.' )

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

                print( str(time())+' '+self.name+': "'+src_msg.type+'" record not found for '+src_msg.name+'. Sending "'+src_msg.type+'" request to 127.0.0.1:'+str(auth_port)+'.' )
                self._socket.sendto( auth_msg.encode(), ('127.0.0.1', auth_port) )
                return
                
            # If not found, let the sender know
            #
            else:
                ret_msg = DnsMessage( src_msg.tid, src_msg.is_response, src_msg.type, src_msg.name, 'Record not found' )
                print( str(time())+' '+self.name+': No '+src_msg.type+' record found for '+src_msg.name )

        # Send final response back to client 
        #
        print( str(time())+' '+self.name+': Sending response to '+src_address[0]+':'+str(src_address[1])+': '+ret_msg.value+'.' )
        self._socket.sendto( ret_msg.encode(), src_address )

    # ============================================
    # ============================================
    def _handle_response( self, auth_msg, src_address ):
        if auth_msg.type == 'INVALID':
            del self._pending_queries[auth_msg.tid]
            return;

        print( str(time())+' '+self.name+': Received response from '+src_address[0]+':'+str(src_address[1])+': '+auth_msg.value+'.' )
        
        if auth_msg.value != 'Record not found':
            self.dns_table.append_record( DnsRecord(auth_msg.name, auth_msg.type, auth_msg.value, 60, 0) )

        client_address,client_tid = self._pending_queries[auth_msg.tid]
        del self._pending_queries[auth_msg.tid]
        auth_msg.tid = client_tid
        print( str(time())+' '+self.name+': Sending response to '+client_address[0]+':'+str(client_address[1])+': '+auth_msg.value+'.' )
        self._socket.sendto( auth_msg.encode(), client_address )

    # ============================================
    # ============================================
    def _generate_tid( self ):
        self._tid += 1
        return self._tid
