from dns import *

# ========================================================================
# ========================================================================
def main():
    # Initialize Dns Server
    #
    server = DnsServer( 'viasatserver', 22000 )

    # Initialize resource table for localserver
    #
    server.dns_table.touch_record( DnsRecord('www.viasat.com', 'A', '8.37.96.179', 0, 1) )

    # Main event loop
    #
    while True:
        # Handle incoming DNS messages, ignoring
        # messages that don't meet our format
        #
        server.handle_dns_message()
     
if __name__ == '__main__':
    main()
