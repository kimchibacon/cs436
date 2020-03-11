from dns import DnsRecord, DnsMessage
from socket import *

# ========================================================================
# ========================================================================
def main():
    # Initialize resource table for localserver
    #
    recordTable = DnsTable()
    recordTable['www.csusm.edu:A'] = DnsRecord( 'www.csusm.edu', 'A', '144.37.5.45', 0, 1 )
    recordTable['cc.csusm.edu:A'] = DnsRecord( 'cc.csusm.edu', 'A', '144.37.5.117', 0, 1 )
    recordTable['cc1.csusm.edu:CNAME'] = DnsRecord( 'cc1.csusm.edu', 'CNAME', 'cc.csusm.edu', 0, 1 )
    recordTable['cc1.csusm.edu:A'] = DnsRecord( 'cc1.csusm.edu', 'A', '144.37.5.118', 0, 1 )
    recordTable['my.csusm.edu:A'] = DnsRecord( 'my.csusm.edu', 'A', '144.37.5.150', 0, 1 )
    recordTable['qualcomm.com:NS'] = DnsRecord( 'qualcomm.com', 'NS', 'dns.qualcomm.edu', 0, 1 )
    recordTable['viasat.com:NS'] = DnsRecord( 'viasat.com', 'NS', 'dns.viasat.edu', 0, 1 )
    recordTable['test'] = DnsRecord( 'test', 'A', 'test', 60, 0 )

    # Bind to socket
    #
    serverPort = 15000
    serverSocket = socket( AF_INET, SOCK_DGRAM )
    serverSocket.bind( ('127.0.0.1', serverPort) )
    print( 'localserver ready...' )

    # Main event loop
    #
    while True:
        # Handle incoming messages
        #
        encMessage, clientAddress = serverSocket.recvfrom( 2048 )
        message = encMessage.decode()

        # Validate message
        #

        # Check local table for record name
        #

        # Instantiate new DnsMessage Object

        # If local record doesn't exist:
        #

            # Look up authoritative DNS server
            #

            # Create query message
            #

            # Send Query message to authoritative server
            #

            # Receive response message
            #

            # If response message contains record
            #
                # Initialize DnsMessage object with response data
                
            # Else
            #
                # Initialize DnsMessage with "Not Found error code"

        # If local record exists:
        #
            # Initialize DnsMessage object with response data

        # Send DnsMessage back to client
        #

    
     
if __name__ == '__main__':
    main()
