from socket import *

serverName = '127.0.0.1'
serverPort = 60000
clientSocket = socket( AF_INET, SOCK_DGRAM )

message = input( 'To Server: ' )
clientSocket.sendto( message.encode(), (serverName, serverPort) )
modifiedMessage, serverAddress = clientSocket.recvfrom( 2048 )

print( 'From Server:', modifiedMessage.decode() )
clientSocket.close()