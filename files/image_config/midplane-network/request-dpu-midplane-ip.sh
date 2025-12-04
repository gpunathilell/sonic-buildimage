#!/bin/bash
#
# request-dpu-midplane-ip.sh
#
# Script to request DHCP IP address for the DPU midplane interface
#

INTERFACE="eth0-midplane"

# Check if the interface is a DPU interface
if ! python3 -c "from utilities_common.chassis import is_dpu; print(is_dpu())" | grep "True"; then
    echo "Not a DPU device. Skipping DHCP request."
    exit 0
fi

# Check if the interface exists
if ip link show "$INTERFACE" 2> /dev/null; then
    echo "Interface $INTERFACE found. Requesting IP address via DHCP..."
    
    # Release existing DHCP lease
    echo "Releasing DHCP lease for $INTERFACE"
    /usr/sbin/dhclient -r "$INTERFACE"
    
    # Wait a moment before requesting new lease
    sleep 1
    
    # Request new DHCP lease
    echo "Requesting DHCP lease for $INTERFACE"
    /usr/sbin/dhclient "$INTERFACE"
    
    echo "DHCP request completed for $INTERFACE"
else
    echo "Interface $INTERFACE not found. Skipping DHCP request."
    exit 0
fi

exit 0

