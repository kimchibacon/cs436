from socket import *
from dns import DnsRecord,DnsMessage,DnsTable

server_name = '127.0.0.1'
server_port = 15000
dns_table = DnsTable()

client_socket = socket( AF_INET, SOCK_DGRAM )

while True:
    hostname = input( 'Enter hostname/domain name: ' )
    rtype = input( 'Enter DNS query type (A, AAAA, CNAME, NS):' )
    msg = DnsMessage( 1, False, rtype, hostname, '' )

    key = msg.name+':'+msg.type
    output = None
    
    if key in dns_table.rr.keys():
        record = dns_table.rr[key]
        print( 'client: Found "'+rtype+'" record for "'+hostname+'" in local DNS table.' )
        output = 'Response: '+record.name+', '+record.type+': '+record.value+'.'
    else:
        client_socket.sendto( msg.encode(), (server_name, server_port) )
        response, server_address = client_socket.recvfrom( 2048 )
        response = DnsMessage.decode_message( response ) 
        output = 'Response: '+response.name+', '+response.type+': '+response.value+'.'

        if response.type == 'INVALID':
            print( 'That was an invalid query!\n' )
            continue
        elif response.value != 'Record not found':
            dns_table.append_record( DnsRecord(response.name, response.type, response.value, 60, 0) )

    print( output )
    dns_table.print_table()

client_socket.close()
