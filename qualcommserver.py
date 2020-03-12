from dns import *

# ========================================================================
# ========================================================================
def main():
    # Initialize Dns Server
    #
    server = DnsServer( 'qualcommserver', 21000 )

    # Initialize resource table for localserver
    #
    server.dns_table.append_record( DnsRecord('www.qualcomm.com', 'A', '104.86.224.205', 0, 1) )
    server.dns_table.append_record( DnsRecord('qtiack12.qti.qualcomm.com', 'A', '129.46.100.21', 0, 1) )

    # Main event loop
    #
    while True:
        # Handle incoming DNS messages, ignoring
        # messages that don't meet our format
        #
        server.handle_dns_message()
     
if __name__ == '__main__':
    main()
