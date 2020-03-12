from socket import *
from dns import DnsRecord,DnsMessage,DnsTable
from time import time

serverName = '127.0.0.1'
serverPort = 15000
dns_table = DnsTable()

clientSocket = socket( AF_INET, SOCK_DGRAM )

while True:
    hostname = input( 'Enter hostname/domain name: ' )
    rtype = input( 'Enter DNS query type (A, AAAA, CNAME, NS):' )
    msg = DnsMessage( 1, False, rtype, hostname, '' )

    key = msg.name+':'+msg.type
    output = None
    if key in dns_table.rr.keys():
        print( str(time())+' client: Found record in local DNS table.' )
        record = dns_table.rr[key]
        output = record.name+': '+record.value
    else:
        clientSocket.sendto( msg.encode(), (serverName, serverPort) )
        response, serverAddress = clientSocket.recvfrom( 2048 )
        response = DnsMessage.decode_message( response )
        dns_table.touch_record( DnsRecord(response.name, response.type, response.value, 60, 0) )
        output = response.name+': '+response.value

    print( response.name+': '+response.value )

clientSocket.close()
