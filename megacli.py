#!/usr/bin/env python2.6
# coding: utf-8

import os

megacli = '/opt/MegaRAID/MegaCli/MegaCli64'

def get_raid_info():
    """Get raid configuration.
    Args:
        
    Return:
        
    Exception:
    """

    # Virtual Disk: 2 (target id: 1)
    # Virtual Drive: 2    // another syntax
    # RAID Level: Primary-5, Secondary-0, RAID Level Qualifier-3
    # Size:5273600MB
    # State: Optimal
    # Stripe Size: 64kB
    # Current Cache Policy: WriteBack ReadAdaptive Direct
    # Slot Number: 10
    # Device Id: 0
    # Media Error Count: 0
    # Raw Size: 953869MB [0x74706db0 Sectors]
    # Non Coerced Size: 953357MB [0x74606db0 Sectors]
    # Coerced Size: 953344MB [0x74600000 Sectors]
    # Inquiry Data: SEAGATE ST31000424SS    KS659WK0Z3RZ
    # Slot Number: 11
    # Device Id: 1
    # Raw Size: 953869MB [0x74706db0 Sectors]
    # Non Coerced Size: 953357MB [0x74606db0 Sectors]
    # Coerced Size: 953344MB [0x74600000 Sectors]
    # Inquiry Data: SEAGATE ST31000424SS    KS659WK0Z34P
    # Device Id: 2

    keys = [ "Device Id",
             "Inquiry Data",
             "Virtual Disk",
             "Virtual Drive",
             "RAID Level *",
             "Firmware state",
             "Media Error Count",
             "Size",
             "State",
             "Current Cache Policy",
             "Slot Number",
             "PD", ]

    keys = [ x + ": " for x in keys ]

    cmd = megacli + ( ' -LdPdInfo  -aAll | grep "%s"' % ( "\|".join( keys ),  ) )

    megalines = shellcmd( cmd ).strip().split( "\n" )
    megalines = [ x for x in megalines if x != '' ]

    vds = {}
    vd = None
    pds = {}
    pd = None

    for line in megalines:

        elts = line.strip().split(':', 1)
        elts = [ x.strip() for x in elts ]

        ( k, v ) = elts
        if k == 'Virtual Disk' \
                or k == 'Virtual Drive':
            # Virtual Disk: 10 (target id: 10)

            vs = v.split( ' ', 1 )

            if len( vs ) == 1:
                raise UnspportedVirtualDiskID( v )

            targetid = vs[ 1 ].split( ' ' )[ -1 ][ :-1 ]
            try:
                int( targetid )
            except Exception, e:
                raise UnspportedVirtualDiskID( v, targetid )

            vd = { 'id' : int( targetid ), 'physicalDisks':{} }

            if vds.has_key( targetid ):
                raise DuplicatedVirtualDisk( targetid )

            vds[ targetid ] = vd

        elif k.startswith( 'RAID Level' ):
            vd[ 'level' ] = [ int( x.strip()[ -1 ] )
                              for x in v.split( ',' )[ :2 ] ]
        elif k == 'Size':
            # vd[ 'size' ] = int( v[ :-2 ] ) * 1024 * 1024
            vd[ 'size' ] = parse_size( v )

        elif k == 'State':
            vd[ 'state' ] = v

        elif k == 'Current Cache Policy':
            vd[ 'policy' ] = v

        elif k == 'PD':
            pd = {}
            pds[ v ] = pd

        elif k == 'Slot Number':
            pd[ 'slotNumber' ] = int( v )

        elif k == 'Device Id':
            pd[ 'id' ] = int( v )
            vd[ 'physicalDisks' ][ v ] = pd

        elif k == 'Firmware state':
            pd[ 'firmwareState' ] = [ x.strip()
                                      for x in v.split( ',' ) ]

        elif k == 'Media Error Count':
            pd[ 'mediaError' ] = int( v )

        elif k == 'Coerced Size':
            pd[ 'size' ] = parse_size( v )

        elif k == 'Inquiry Data':
            info = [ x.strip() for x in v.split( ' ' ) if x != '' ]

            # IBM-ESXSCBRCA146C3ETS0 write vendor and model together

            if len( info ) == 2 and info[ 0 ].startswith( 'IBM' ):
                pd[ 'vendor' ], pd[ 'model' ], pd[ 'serial' ] = info[ 0 ].split( '-', 1 ) + info[ 1: ]

            elif len( info ) == 4:
                if info[ 0 ] == 'ATA':
                    # Inquiry Data: ATA     ST32000644NS    BB28            9WM575H9
                    pd[ 'vendor' ], pd[ 'model' ], pd[ 'serial' ] = [ 'SEAGATE', info[ 1 ], info[ 3 ] ]

                elif info[ 2 ] == '42D0791IBM':
                    # Inquiry Data:             9WM5750AST32000644NS         42D0788 42D0791IBM BB28
                    pd[ 'vendor' ], pd[ 'model' ], pd[ 'serial' ] = [ 'IBM', info[ 1 ], info[ 0 ] ]

                else:
                    raise UnspportedInquiry( v )
            else:
                pd[ 'vendor' ], pd[ 'model' ], pd[ 'serial' ] = info

    return ( vds, pds )

def shellcmd( cmd ):
    return os.popen( cmd ).read()

if __name__ == '__main__':

    import pprint

    pprint.pprint( get_raid_info() )
