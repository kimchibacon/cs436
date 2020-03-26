from socket import *
from dns import DnsTable
import pickle

server_name = '127.0.0.1'
server_port = 15000
dns_table = DnsTable()

admin_socket = socket( AF_INET, SOCK_DGRAM )

# This is effectively a password sent in the clear
# to let the server know that this is an admin request.
# It's handled in DnsServer.handle_dns_message().
# Dumb idea for the real world, but it works easily
# for our assignment.
#
admin_msg = 'ADMIN IN THE CLEAR'

admin_socket.sendto( admin_msg.encode(), (server_name, server_port) )
response, server_address = admin_socket.recvfrom( 2048 )

# The server will recognize the admin request
# and respond with the entire table as a Byte()
# object using the pickle library. Simply
# use the pickle library to decode that table.
#
dns_table.rr = pickle.loads( response )

print( '\n\'localserver\' DNS table:' )
dns_table.print_table()

admin_socket.close()
dns_table.destroy()
