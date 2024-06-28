"""Input Data for dpuctl tests"""
testData = {
             'PW_OFF': {'AssertionError':
                        {'arg_list': [['dpu5'],
                                      ['dpu1', '--all'],
                                      ['dpu1,dpu2,dpu3,dpu5'],
                                      ['dpu5', '--all'],
                                      ['dpu5', '--all', '--force'],
                                      ]},
                        'Returncheck':
                        {'arg_list': [['dpu1'],
                                      ['dpu1, dpu2,dpu3', '--force'],
                                      ['--all', '--force'],
                                      ['dpu4', '--path'],
                                      ['--all', '--test'],
                                      ],
                         'rc': [0, 0, 0, 2, 2],
                         'return_message': ["",
                                            "",
                                            "",
                                            "Usage: dpu-power-off [OPTIONS]"
                                            " <dpu_names>\n"
                                            "Try 'dpu-power-off --help' for"
                                            " help.\n\nError: "
                                            "No such option: --path\n",
                                            "Usage: dpu-power-off [OPTIONS] "
                                            "<dpu_names>\n"
                                            "Try 'dpu-power-off --help' for"
                                            " help.\n\n"
                                            "Error: No such option: --test\n"],
                         }
                        },
             'PW_ON': {'AssertionError':
                       {'arg_list': [['dpu5'],
                                     ['dpu1', '--all'],
                                     ['dpu1,dpu2,dpu3,dpu5'],
                                     ['dpu5', '--all'],
                                     ['dpu5', '--all', '--force'],
                                     ]},
                       'Returncheck':
                       {'arg_list': [['dpu1'],
                                     ['dpu1,dpu2,dpu3', '--force'],
                                     ['--all'],
                                     ['--all', '--force'],
                                     ['dpu4', '--path'],
                                     ['--all', '--test'],
                                     ],
                        'rc': [0, 0, 0, 0, 2, 2],
                        'return_message': ["",
                                           "",
                                           "",
                                           "",
                                           "Usage: dpu-power-on [OPTIONS]"
                                           " <dpu_names>\n"
                                           "Try 'dpu-power-on --help'"
                                           " for help.\n\nError: "
                                           "No such option: --path\n",
                                           "Usage: dpu-power-on [OPTIONS]"
                                           " <dpu_names>\n"
                                           "Try 'dpu-power-on --help'"
                                           " for help.\n\nError: "
                                           "No such option: --test\n"],
                        }
                       },
             'RST': {'AssertionError':
                     {'arg_list': [['dpu5'],
                                   ['dpu1', '--all'],
                                   ['dpu1,dpu2,dpu3,dpu5'],
                                   ['dpu5', '--all'],
                                   ['dpu1,dpu5', '--all'],
                                   ]},
                     'Returncheck':
                     {'arg_list': [['dpu1'],
                                   ['dpu1,dpu2,dpu3', '--force'],
                                   ['--all'],
                                   ['--all', '--force'],
                                   ['dpu1,dpu2,dpu3'],
                                   ['--all', '--test'],
                                   ],
                      'rc': [0, 2, 0, 2, 0, 2],
                      'return_message': ["",
                                         "Usage: dpu-reset [OPTIONS]"
                                         " <dpu_names>\n"
                                         "Try 'dpu-reset --help'"
                                         " for help.\n\nError: "
                                         "No such option: --force\n",
                                         "",
                                         "Usage: dpu-reset [OPTIONS]"
                                         " <dpu_names>\n"
                                         "Try 'dpu-reset --help' for help."
                                         "\n\nError: "
                                         "No such option: --force\n",
                                         "",
                                         "Usage: dpu-reset [OPTIONS]"
                                         " <dpu_names>\n"
                                         "Try 'dpu-reset --help' for help."
                                         "\n\nError: "
                                         "No such option: --test\n"],
                      }
                     },
             'FW_UPG': {'AssertionError':
                        {'arg_list': [['dpu5', '--path', 'abc'],
                                      ['dpu1', '--all', '--path', 'abc'],
                                      ['dpu1,dpu2,dpu3,dpu5', '--path', 'abc'],
                                      ['dpu5', '--all', '--path', 'abc'],
                                      ['dpu1,dpu5', '--all', '--path', 'abc'],
                                      ]},
                        'Returncheck':
                        {'arg_list': [['dpu1', '--path', 'abc'],
                                      ['dpu1,dpu2,dpu3', '--force'],
                                      ['--all'],
                                      ['--all', '--path', 'abc'],
                                      ['dpu1,dpu2,dpu3', '--path', 'abc'],
                                      ['--all', '--test'],
                                      ],
                         'rc': [0, 2, 2, 0, 0, 2],
                         'return_message': ["",
                                            "Usage: dpu-fw-upgrade [OPTIONS]"
                                            " <dpu_names>\n"
                                            "Try 'dpu-fw-upgrade --help'"
                                            " for help.\n\nError: "
                                            "No such option: --force\n",
                                            "Usage: dpu-fw-upgrade [OPTIONS]"
                                            " <dpu_names>\n"
                                            "Try 'dpu-fw-upgrade --help'"
                                            " for help.\n\n"
                                            "Error: Missing option "
                                            "'--path'.\n",
                                            "",
                                            "",
                                            "Usage: dpu-fw-upgrade "
                                            "[OPTIONS] <dpu_names>\n"
                                            "Try 'dpu-fw-upgrade --help'"
                                            " for help.\n\nError: "
                                            "No such option: --test\n"],
                         }
                        },
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
