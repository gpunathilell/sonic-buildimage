#
# Copyright (c) 2021 NVIDIA CORPORATION & AFFILIATES.
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

import os
import sys
if sys.version_info.major == 3:
    from unittest import mock
    from mock import patch
else:
    import mock
    from mock import patch
import sonic_platform.utils
from swsscommon import swsscommon
test_path = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.dirname(test_path)
sys.path.insert(0, modules_path)
swsscommon.ConfigDBConnector = mock.MagicMock()

import sonic_platform.chassis
from sonic_platform import utils
from sonic_platform.chassis import ModularChassis, SmartSwitchChassis
from sonic_platform.device_data import DeviceDataManager
from sonic_platform.module import Module
from sonic_platform_base.module_base import ModuleBase


class TestModule:
    @classmethod
    def setup_class(cls):
        DeviceDataManager.get_linecard_sfp_count = mock.MagicMock(return_value=2)
        DeviceDataManager.get_linecard_count = mock.MagicMock(return_value=2)
        DeviceDataManager.get_dpu_count = mock.MagicMock(return_value=4)
        sonic_platform.chassis.extract_RJ45_ports_index = mock.MagicMock(return_value=[])

    def test_chassis_get_num_sfp(self):
        chassis = ModularChassis()
        assert chassis.get_num_sfps() == 4

    def test_chassis_get_num_modules(self):
        chassis = SmartSwitchChassis()
        assert chassis.get_num_modules() == 4

    def test_chassis_get_all_sfps(self):
        utils.read_int_from_file = mock.MagicMock(return_value=1)
        chassis = ModularChassis()
        assert len(chassis.get_all_sfps()) == 4

    @mock.patch('sonic_platform.device_data.DeviceDataManager.get_linecard_max_port_count', mock.MagicMock(return_value=16))
    def test_chassis_get_sfp(self):
        utils.read_int_from_file = mock.MagicMock(return_value=1)
        index = 1
        chassis = ModularChassis()
        sfp = chassis.get_sfp(index)
        assert sfp

    def test_thermal(self):
        from sonic_platform.thermal import THERMAL_NAMING_RULE
        DeviceDataManager.get_gearbox_count = mock.MagicMock(return_value=2)
        utils.read_int_from_file = mock.MagicMock(return_value=1)
        m = Module(1)
        assert m.get_num_thermals() == 2
        assert len(m._thermal_list) == 0

        thermals = m.get_all_thermals()
        assert len(thermals) == 2

        rule = THERMAL_NAMING_RULE['linecard thermals']
        start_index = rule.get('start_index', 1)
        for i, thermal in enumerate(thermals):
            assert rule['name'].format(i + start_index) in thermal.get_name()
            assert rule['temperature'].format(i + start_index) in thermal.temperature
            assert rule['high_threshold'].format(i + start_index) in thermal.high_threshold
            assert rule['high_critical_threshold'].format(i + start_index) in thermal.high_critical_threshold
            assert thermal.get_position_in_parent() == i + 1

        thermal = m.get_thermal(1)
        assert thermal
        assert thermal.get_position_in_parent() == 2

    def get_sfp(self):
        DeviceDataManager.get_linecard_sfp_count = mock.MagicMock(return_value=3)
        utils.read_int_from_file = mock.MagicMock(return_value=1)
    
        # Test get_num_sfps, it should not create any SFP objects
        m = Module(1)
        assert m.get_num_sfps() == 3
        assert len(m._sfp_list) == 0

        # Index out of bound, return None
        sfp = m.get_sfp(3)
        assert sfp is None
        assert len(m._sfp_list) == 0

        # Get one SFP, other SFP list should be initialized to None
        sfp = m.get_sfp(0)
        assert sfp is not None
        assert len(m._sfp_list) == 3
        assert m._sfp_list[1] is None
        assert m._sfp_list[2] is None
        assert m.sfp_initialized_count == 1

        # Get the SFP again, no new SFP created
        sfp1 = m.get_sfp(0)
        assert id(sfp) == id(sfp1)

        # Get another SFP, sfp_initialized_count increase
        sfp2 = m.get_sfp(1)
        assert sfp2 is not None
        assert m._sfp_list[2] is None
        assert m.sfp_initialized_count == 2

        # Get all SFPs, but there are SFP already created, only None SFP created
        sfp_list = m.get_all_sfps()
        assert len(sfp_list) == 3
        assert m.sfp_initialized_count == 3
        assert filter(lambda x: x is not None, sfp_list)
        assert id(sfp1) == id(sfp_list[0])
        assert id(sfp2) == id(sfp_list[1])

        # Get all SFPs, no SFP yet, all SFP created
        m._sfp_list = []
        m.sfp_initialized_count = 0
        sfp_list = m.get_all_sfps()
        assert len(sfp_list) == 3
        assert m.sfp_initialized_count == 3

    def test_check_state(self):
        utils.read_int_from_file = mock.MagicMock(return_value=0)
        m = Module(1)
        m._sfp_list.append(1)
        m._thermal_list.append(1)
        m._get_seq_no = mock.MagicMock(return_value=0)
        # both seq number and state no change, do not re-init module 
        m._check_state()
        assert len(m._sfp_list) > 0
        assert len(m._thermal_list) > 0

        # seq number changes, but state keeps deactivated, no need re-init module 
        m._get_seq_no = mock.MagicMock(return_value=1)
        m._check_state()
        assert len(m._sfp_list) > 0
        assert len(m._thermal_list) > 0

        # seq number not change, state changes from deactivated to activated, need re-init module
        utils.read_int_from_file = mock.MagicMock(return_value=1)
        m._check_state()
        assert len(m._sfp_list) == 0
        assert len(m._thermal_list) == 0

        # seq number changes, state keeps activated, which means the module has been replaced, need re-init module
        m._sfp_list.append(1)
        m._thermal_list.append(1)
        m._get_seq_no = mock.MagicMock(return_value=2)
        m._check_state()
        assert len(m._sfp_list) == 0
        assert len(m._thermal_list) == 0

        # seq number not change, state changes from activated to deactivated, need re-init module
        m._sfp_list.append(1)
        m._thermal_list.append(1)
        utils.read_int_from_file = mock.MagicMock(return_value=0)
        m._check_state()
        assert len(m._sfp_list) == 0
        assert len(m._thermal_list) == 0

    @patch('swsscommon.swsscommon.ConfigDBConnector', mock.MagicMock())
    @patch('swsscommon.swsscommon.ConfigDBConnector.connect', mock.MagicMock())
    def test_module_vpd(self):
        from sonic_platform.module import DpuModule
        m = Module(1)
        m.vpd_parser.vpd_file = os.path.join(test_path, 'mock_psu_vpd')

        assert m.get_model() == 'MTEF-PSF-AC-C'
        assert m.get_serial() == 'MT1946X07684'
        assert m.get_revision() == 'A3'

        m.vpd_parser.vpd_file = 'not exists'
        assert m.get_model() == 'N/A'
        assert m.get_serial() == 'N/A'
        assert m.get_revision() == 'N/A'

        m.vpd_parser.vpd_file_last_mtime = None
        m.vpd_parser.vpd_file = os.path.join(test_path, 'mock_psu_vpd')
        assert m.get_model() == 'MTEF-PSF-AC-C'
        assert m.get_serial() == 'MT1946X07684'
        assert m.get_revision() == 'A3'

        dm = DpuModule(2)
        dm.vpd_parser.vpd_file_last_mtime = None
        dm.vpd_parser.vpd_file = os.path.join(test_path, 'mock_psu_vpd_dpu')
        print(dm.vpd_parser.vpd_file)
        assert dm.get_base_mac() == "90:0A:84:C6:00:B1"

    @patch('swsscommon.swsscommon.ConfigDBConnector', mock.MagicMock())
    @patch('swsscommon.swsscommon.ConfigDBConnector.connect', mock.MagicMock())
    def test_dpu_module(self):
        from sonic_platform.module import DpuModule
        m = DpuModule(3)
        assert m.get_type() == ModuleBase.MODULE_TYPE_DPU
        assert m.get_name() == "DPU3"
        assert m.get_description() == "NVIDIA BlueField-3 DPU"
        assert m.get_dpu_id() == 3
        m.dpuctl_obj.dpu_reboot = mock.MagicMock(return_value = True)
        assert m.reboot(ModuleBase.MODULE_REBOOT_DEFAULT) == True
        m.dpuctl_obj.dpu_power_on = mock.MagicMock(return_value = True)
        assert m.set_admin_state(True) == True
        assert m.fault_state == False
        m.dpuctl_obj.dpu_power_on = mock.MagicMock(return_value = False)
        assert m.set_admin_state(True) == False
        assert m.fault_state == True
        assert m.get_oper_status() == ModuleBase.MODULE_STATUS_FAULT
        m.dpuctl_obj.dpu_power_off = mock.MagicMock(return_value = True)
        assert m.set_admin_state(False) == True
        m.fault_state = False
        test_file_path = ""
        def mock_read_int_from_file(file_path, default=0, raise_exception=False, log_func=None):
            if file_path.endswith(test_file_path):
                return 1
            else:
                return 0
        with patch("sonic_platform.utils.read_int_from_file",wraps=mock_read_int_from_file) as mock_read:
            test_file_path = "dpu3_ready"
            assert m.get_oper_status() == ModuleBase.MODULE_STATUS_ONLINE
            test_file_path = "dpu3_shtdn_ready"
            assert m.get_oper_status() == ModuleBase.MODULE_STATUS_OFFLINE