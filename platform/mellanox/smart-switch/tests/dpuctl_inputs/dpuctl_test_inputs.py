"""Input Data for dpuctl tests"""
testData = {
             'PW_OFF': {'AssertionError':
                        {'arg_list': [['dpu5'],
                                      ['dpu1', '--all',],
                                      ['dpu1,dpu2,dpu3,dpu5'],
                                      ['dpu5', '--all'],
                                      ['dpu5', '--all', '--force'],
                                      ]},
                        'Returncheck':
                        {'arg_list': [['dpu1'],
                                      ['dpu1, dpu2,dpu3', '--force',],
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
                                     ['dpu1', '--all',],
                                     ['dpu1,dpu2,dpu3,dpu5'],
                                     ['dpu5', '--all'],
                                     ['dpu5', '--all', '--force'],
                                     ]},
                       'Returncheck':
                       {'arg_list': [['dpu1'],
                                     ['dpu1,dpu2,dpu3', '--force',],
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
             'SHTDN': {'AssertionError':
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
                                           "Usage: dpu-shutdown "
                                           "[OPTIONS] <dpu_names>\n"
                                           "Try 'dpu-shutdown --help"
                                           "' for help.\n\nError: "
                                           "No such option: --force\n",
                                           "",
                                           "Usage: dpu-shutdown "
                                           "[OPTIONS] <dpu_names>\n"
                                           "Try 'dpu-shutdown --help'"
                                           " for help.\n\nError: "
                                           "No such option: --force\n",
                                           "",
                                           "Usage: dpu-shutdown "
                                           "[OPTIONS] <dpu_names>\n"
                                           "Try 'dpu-shutdown --help'"
                                           " for help.\n\nError: "
                                           "No such option: --test\n"],
                        }
                       },
             'STRTUP': {'AssertionError':
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
                                            "Usage: dpu-startup "
                                            "[OPTIONS] <dpu_names>\n"
                                            "Try 'dpu-startup --help'"
                                            " for help.\n\nError: "
                                            "No such option: --force\n",
                                            "",
                                            "Usage: dpu-startup "
                                            "[OPTIONS] <dpu_names>\n"
                                            "Try 'dpu-startup --help'"
                                            " for help.\n\nError: "
                                            "No such option: --force\n",
                                            "",
                                            "Usage: dpu-startup "
                                            "[OPTIONS] <dpu_names>\n"
                                            "Try 'dpu-startup --help' "
                                            "for help.\n\nError: "
                                            "No such option: --test\n"],
                         }
                        },
}
