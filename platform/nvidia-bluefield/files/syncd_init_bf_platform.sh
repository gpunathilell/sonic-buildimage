#!/bin/bash
#
# Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES.
# Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

configure_syncd_init_common() {
    # Read MAC addresses
    base_mac="$(echo $SYNCD_VARS | jq -r '.mac')"
    hwsku=$(sonic-cfggen -d -v 'DEVICE_METADATA["localhost"]["hwsku"]')
    platform=$(sonic-cfggen -d -v 'DEVICE_METADATA["localhost"]["platform"]')
    single_port=$([[ $hwsku == *"-com-dpu" ]] && echo true || echo false)
    # Read MAC addresses
    base_mac="$(echo $SYNCD_VARS | jq -r '.mac')"
    hwsku=$(sonic-cfggen -d -v 'DEVICE_METADATA["localhost"]["hwsku"]')
    platform=$(sonic-cfggen -d -v 'DEVICE_METADATA["localhost"]["platform"]')
    single_port=$([[ $hwsku == *"-com-dpu" ]] && echo true || echo false)

    eth0_mac=$(cat /sys/class/net/Ethernet0/address)

    cp $HWSKU_DIR/sai.profile /tmp/sai-temp.profile

    echo >> /tmp/sai-temp.profile

    DEVICE_TYPE=$(/usr/bin/asic_detect/asic_detect.sh)
    if [[ $? -eq 0 ]]; then
        ASIC_PROFILE_FILE="sai-${DEVICE_TYPE}.profile"
        ASIC_PROFILE_PATH="/etc/mlnx/${ASIC_PROFILE_FILE}"
        if [ -f "$ASIC_PROFILE_PATH" ]; then
            cat "$ASIC_PROFILE_PATH" >> /tmp/sai-temp.profile
            echo >> /tmp/sai-temp.profile
        fi
    else
        echo "Warning: ASIC is not detected..."
    fi

    # keep only the first occurence of each prefix with '=' sign, and remove the others.
    awk -F= '!seen[$1]++' /tmp/sai-temp.profile > /tmp/sai.profile
    rm -f /tmp/sai-temp.profile

    # Update sai.profile with MAC_ADDRESS
    echo "DEVICE_MAC_ADDRESS=$base_mac" >> /tmp/sai.profile
    echo "PORT_1_MAC_ADDRESS=$eth0_mac" >> /tmp/sai.profile

    CMD_ARGS+=" -l -p /tmp/sai.profile -w 180000000"

    SDK_DUMP_PATH=$(cat /tmp/sai.profile | grep "SAI_DUMP_STORE_PATH" | cut -d = -f2)
    if [ ! -d "$SDK_DUMP_PATH" ]; then
        mkdir -p "$SDK_DUMP_PATH"
    fi

    platform_json_path="/mnt/$image_dir/platform/$platform/platform.json"

    hugepages=$(jq -r '.HUGEPAGES' $platform_json_path)
    if [ -z "$hugepages" ]; then
        hugepages=9216
    fi

    echo $hugepages > /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages

    mkdir -p /mnt/huge
    mount -t hugetlbfs pagesize=1GB /mnt/huge

    ethtool -A Ethernet0 rx off tx off
}
