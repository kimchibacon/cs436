from dns import *

# ========================================================================
# ========================================================================
def main():
    # Initialize Dns Server
    #
    server = DnsServer( 'localserver', 15000 )

    # Initialize resource table for localserver
    #
    server.dns_table.touch_record( DnsRecord('www.csusm.edu', 'A', '144.37.5.45', 0, 1) )
    server.dns_table.touch_record( DnsRecord('cc.csusm.edu', 'A', '144.37.5.117', 0, 1) )
    server.dns_table.touch_record( DnsRecord('cc1.csusm.edu', 'CNAME', 'cc.csusm.edu', 0, 1) )
    server.dns_table.touch_record( DnsRecord('cc1.csusm.edu', 'A', '144.37.5.118', 0, 1) )
    server.dns_table.touch_record( DnsRecord('my.csusm.edu', 'A', '144.37.5.150', 0, 1) )
    server.dns_table.touch_record( DnsRecord('qualcomm.com', 'NS', 'dns.qualcomm.edu', 0, 1) )
    server.dns_table.touch_record( DnsRecord('viasat.com', 'NS', 'dns.viasat.edu', 0, 1) )

    # Main event loop
    #
    while True:
        # Handle incoming DNS messages, ignoring
        # messages that don't meet our format
        #
        server.handle_dns_message()
     
if __name__ == '__main__':
    main()
