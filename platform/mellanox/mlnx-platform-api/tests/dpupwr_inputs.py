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
