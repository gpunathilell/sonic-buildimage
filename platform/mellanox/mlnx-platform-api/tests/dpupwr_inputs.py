#
# Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES.
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

"""Input Data for dpuctl tests"""
testData = {
             'power_off': ["dpu1: Power off forced=True\nAn error occurred: "
                           "FileNotFoundError - dpu1:"
                           "File /var/run/hw-management"
                           "/system/dpu1_pwr_force does not exist!\n",
                           "dpu1: Power off forced=False\nAn error occurred: "
                           "FileNotFoundError - dpu1:"
                           "File /var/run/hw-management"
                           "/system/dpu1_rst does not exist!\n",
                           ],
             'power_on': ["dpu1: Power on forced=True\nAn error occurred: "
                          "FileNotFoundError - dpu1:"
                          "File /var/run/hw-management"
                          "/system/dpu1_pwr_force does not exist!\n",
                          "dpu1: Power on forced=False\nAn error occurred: "
                          "FileNotFoundError - dpu1:File "
                          "/var/run/hw-management"
                          "/system/dpu1_pwr does not exist!\n",
                          ],
             'reset': ["dpu1: Reboot\nAn error occurred: "
                       "FileNotFoundError - dpu1:File /sys/bus/pci/devices/"
                       "dpu1_pciid/remove does not exist!\n",
                       ],
             'fw_upgrade': ["dpu1: FW upgrade\nAn error occurred: "
                            "FileNotFoundError - dpu1:File "
                            "/sys/bus/pci/devices/"
                            "dpu1_id/remove does not exist!\n",
                            ],
}
