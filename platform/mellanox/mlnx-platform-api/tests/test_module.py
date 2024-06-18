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
import pytest
import sonic_platform.utils
import subprocess
test_path = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.dirname(test_path)
sys.path.insert(0, modules_path)
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

    @mock.patch('swsscommon.swsscommon.SonicV2Connector.__init__', mock.MagicMock(return_value=None))
    @mock.patch('swsscommon.swsscommon.SonicV2Connector.connect', mock.MagicMock(return_value=None))
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

    @mock.patch('swsscommon.swsscommon.SonicV2Connector.__init__', mock.MagicMock(return_value=None))
    @mock.patch('swsscommon.swsscommon.SonicV2Connector.connect', mock.MagicMock(return_value=True))
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
        dm.dpu_vpd_parser.vpd_file_last_mtime = None
        dm.dpu_vpd_parser.vpd_file = os.path.join(test_path, 'mock_psu_vpd_dpu')
        assert dm.get_base_mac() == "90:0A:84:C6:00:B1"
        assert dm.get_model() == "SN4280BF3DPU2"
        assert dm.get_serial() == "MT4431X26022"
        assert dm.get_revision() == "A0"

        dm.dpu_vpd_parser = None
        with pytest.raises(AttributeError):
            dm.get_base_mac()
            dm.get_model()
            dm.get_serial()
            dm.get_revision()

        dm = DpuModule(5)
        dm.dpu_vpd_parser.vpd_file_last_mtime = None
        dm.dpu_vpd_parser.vpd_file = os.path.join(test_path, 'mock_psu_vpd_dpu')
        assert dm.get_base_mac() == "N/A"
        assert dm.get_model() == "N/A"
        assert dm.get_serial() == "N/A"
        assert dm.get_revision() == "N/A"

        m.vpd_parser.vpd_file = 'does not exist'
        assert dm.get_base_mac() == "N/A"
        assert m.get_model() == 'N/A'
        assert m.get_serial() == 'N/A'
        assert m.get_revision() == 'N/A'

    @mock.patch('swsscommon.swsscommon.SonicV2Connector.__init__', mock.MagicMock(return_value=None))
    @mock.patch('swsscommon.swsscommon.SonicV2Connector.connect', mock.MagicMock(return_value=None))
    @mock.patch('swsscommon.swsscommon.SonicV2Connector.get')
    @mock.patch('subprocess.call')
    def test_dpu_module(self, mock_call, mock_get):
        from sonic_platform.module import DpuModule
        m = DpuModule(3)
        assert m.get_type() == ModuleBase.MODULE_TYPE_DPU
        assert m.get_name() == "DPU3"
        assert m.get_description() == "NVIDIA BlueField-3 DPU"
        assert m.get_dpu_id() == 3
        m.dpuctl_obj.dpu_reboot = mock.MagicMock(return_value=True)
        assert m.reboot(ModuleBase.MODULE_REBOOT_DEFAULT) is True
        assert m.reboot("None") is False
        m.dpuctl_obj.dpu_power_on = mock.MagicMock(return_value=True)
        assert m.set_admin_state(True) is True
        assert m.fault_state is False
        m.dpuctl_obj.dpu_power_on = mock.MagicMock(return_value=False)
        assert m.set_admin_state(True) is False
        assert m.fault_state is True
        assert m.get_oper_status() == ModuleBase.MODULE_STATUS_FAULT
        m.dpuctl_obj.dpu_power_off = mock.MagicMock(return_value=True)
        assert m.set_admin_state(False) is True
        midplane_data = {
            "bridge_name": "bridge-midplane",
            "bridge_address": "169.254.200.254/24"
        }
        DeviceDataManager.get_platform_midplane_network = mock.MagicMock(return_value=midplane_data)
        assert m.get_midplane_ip() == "169.254.200.3"
        assert m.midplane_ip == "169.254.200.3"
        m1 = DpuModule(4)
        assert m1.get_midplane_ip() == "169.254.200.4"
        assert m1.midplane_ip == "169.254.200.4"
        m1.midplane_ip = None
        m.midplane_ip = None
        DeviceDataManager.get_platform_midplane_network = mock.MagicMock(return_value=None)
        with pytest.raises(TypeError):
            m.get_midplane_ip()
            m1.get_midplane_ip()
            m.is_midplane_reachable()
            m1.is_midplane_reachable()
        original_function = DpuModule._is_midplane_up
        DpuModule._is_midplane_up = mock.MagicMock(return_value=True)
        DeviceDataManager.get_platform_midplane_network = mock.MagicMock(return_value={})
        m1.midplane_ip = None
        m.midplane_ip = None
        with pytest.raises(KeyError):
            m.get_midplane_ip()
            m1.get_midplane_ip()
            m.is_midplane_reachable()
            m1.is_midplane_reachable()
        # Check if it works for other CIDR notations
        midplane_data = {
            "bridge_name": "bridge-midplane",
            "bridge_address": "169.254.200.254/28"
        }
        DeviceDataManager.get_platform_midplane_network = mock.MagicMock(return_value=midplane_data)
        m1.midplane_ip = None
        m.midplane_ip = None
        assert m.get_midplane_ip() == "169.254.200.243"
        assert m1.get_midplane_ip() == "169.254.200.244"
        command = ['ping', '-c', '1', '-W', '1', "169.254.200.243"]
        mock_call.return_value = 0
        assert m.is_midplane_reachable()
        mock_call.assert_called_with(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        mock_call.return_value = 1
        assert not m.is_midplane_reachable()
        mock_call.assert_called_with(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        mock_call.side_effect = subprocess.CalledProcessError(1, command)
        assert not m.is_midplane_reachable()
        assert not m1.is_midplane_reachable()
        DpuModule._is_midplane_up = mock.MagicMock(return_value=False)
        assert not m.is_midplane_reachable()
        assert not m1.is_midplane_reachable()
        DpuModule._is_midplane_up = original_function

        m.fault_state = False
        test_file_path = ""
        pl_data = {
            "dpu0": {
                "interface": {"Ethernet224": "Ethernet0"},
                "midplane_interface": "dpu0_mid"
            },
            "dpu1": {
                "interface": {"Ethernet232": "Ethernet1"},
                "midplane_interface": "dpu1_mid"
            },
            "dpu2": {
                "interface": {"Ethernet236": "Ethernet2"},
                "midplane_interface": "dpu2_mid"
            },
            "dpu3": {
                "interface": {"EthernetX": "EthernetY"},
                "midplane_interface": "dpu3_mid"
            }
        }
        DeviceDataManager.get_platform_dpus_data = mock.MagicMock(return_value=pl_data)

        def mock_read_int_from_file(file_path, default=0, raise_exception=False, log_func=None):
            if file_path.endswith(test_file_path):
                return 1
            else:
                return 0
        with patch("sonic_platform.utils.read_int_from_file", wraps=mock_read_int_from_file):
            # HW name of DPU3 = dpu4 since HW name starts from dpu1
            test_file_path = "dpu4_ready"
            assert m.get_oper_status() == ModuleBase.MODULE_STATUS_ONLINE
            test_file_path = "dpu3_shtdn_ready"
            assert m.get_oper_status() == ModuleBase.MODULE_STATUS_OFFLINE
            test_file_path = "aaa"
            # Default state is offline
            assert m.get_oper_status() == ModuleBase.MODULE_STATUS_OFFLINE
            test_file_path = "reset_from_main_board"
            assert m.get_reboot_cause() == (ModuleBase.REBOOT_CAUSE_HOST_RESET_DPU, '')
            test_file_path = "reset_dpu_thermal"
            assert m.get_reboot_cause() == (ModuleBase.REBOOT_CAUSE_SW_THERMAL, '')
            test_file_path = "reset_aux_pwr_or_reload"
            assert m.get_reboot_cause() == (ModuleBase.REBOOT_CAUSE_POWER_LOSS, '')
            test_file_path = "reset_pwr_off"
            assert m.get_reboot_cause() == (ModuleBase.REBOOT_CAUSE_DPU_SELF_REBOOT, '')
            test_file_path = "tpm_rst"
            assert m.get_reboot_cause() == (ModuleBase.REBOOT_CAUSE_HARDWARE_OTHER, 'Reset by the TPM module')
            test_file_path = "perst_rst"
            assert m.get_reboot_cause() == (ModuleBase.REBOOT_CAUSE_HARDWARE_OTHER, 'PERST# signal to ASIC')
            test_file_path = "phy_rst"
            assert m.get_reboot_cause() == (ModuleBase.REBOOT_CAUSE_HARDWARE_OTHER, 'Phy reset')
            test_file_path = "usbphy_rst"
            assert m.get_reboot_cause() == (ModuleBase.REBOOT_CAUSE_HARDWARE_OTHER, 'USB Phy reset')
            test_file_path = "None"
            assert m.get_reboot_cause() == (ModuleBase.REBOOT_CAUSE_NON_HARDWARE, '')
        appl_db_data = {
            'PORT_TABLE:Ethernet224': {
                'admin_status': 'up',
                'alias': 'etp1',
                'description': 'ARISTA01T0:Ethernet1',
                'temp_threshold': '100',
                'voltage': '10',
                'oper_status': 'up',
                'voltage_max_threshold': '15',
            },
            'PORT_TABLE:Ethernet232': {
                'admin_status': 'up',
                'alias': 'etp1',
                'description': 'ARISTA01T0:Ethernet5',
                'temp_threshold': '100',
                'voltage': '10',
                'oper_status': 'down',
                'voltage_max_threshold': '15',
            }
        }

        def return_port_status(db1, table, key):
            return appl_db_data[table][key]
        mock_get.side_effect = return_port_status

        m1 = DpuModule(0)
        m2 = DpuModule(1)
        m3 = DpuModule(2)
        m4 = DpuModule(4)
        assert not m1.midplane_interface
        with patch("sonic_platform.utils.read_str_from_file", wraps=mock.MagicMock(return_value="up")):
            assert m1._is_midplane_up()
            assert m2._is_midplane_up()
            assert m3._is_midplane_up()
            with pytest.raises(KeyError):
                m4._is_midplane_up()
            assert m1.midplane_interface == "dpu0_mid"
            assert m2.midplane_interface == "dpu1_mid"
            assert m3.midplane_interface == "dpu2_mid"
        with patch("sonic_platform.utils.read_str_from_file", wraps=mock.MagicMock(return_value="down")):
            assert not m1._is_midplane_up()
            assert not m2._is_midplane_up()
            assert not m3._is_midplane_up()
        assert m1._is_dataplane_online()
        assert not m2._is_dataplane_online()
        with pytest.raises(KeyError):
            m3._is_dataplane_online()
            m4._is_dataplane_online()
        file_path_list = ["dpu1_shtdn_ready", "dpu1_ready"]
        value_list = [1, 0]
        mock_get.side_effect = None
        mock_get.return_value = "down"

        def mock_opp_read_int_from_file(file_path, default=0, raise_exception=False, log_func=None):
            for ind, file_name in enumerate(file_path_list):
                if file_path.endswith(file_name):
                    return value_list[ind]
            return 0
        with patch("sonic_platform.utils.read_int_from_file", wraps=mock_opp_read_int_from_file):
            # Should return offline - as dpu3_shtdn_ready is set and fault_state is off
            assert m1.get_oper_status() == ModuleBase.MODULE_STATUS_OFFLINE
            value_list[1] = 1
            DpuModule.is_midplane_reachable = mock.MagicMock(return_value=False)
            assert m1.get_oper_status() == ModuleBase.MODULE_STATUS_ONLINE
            DpuModule.is_midplane_reachable = mock.MagicMock(return_value=True)
            DpuModule._is_dataplane_online = mock.MagicMock(return_value=False)
            assert m1.get_oper_status() == ModuleBase.MODULE_STATUS_MIDPLANE_ONLINE
            DpuModule._is_dataplane_online = mock.MagicMock(return_value=True)
            assert m1.get_oper_status() == ModuleBase.MODULE_STATUS_CONTROLPLANE_ONLINE
            m1.fault_state = True
            assert m1.get_oper_status() == ModuleBase.MODULE_STATUS_FAULT
            m1.fault_state = False
            value_list[0] = 1
            m1.get_oper_status() == ModuleBase.MODULE_STATUS_OFFLINE
            value_list[0] = 0
            m1.get_oper_status() == ModuleBase.MODULE_STATUS_CONTROLPLANE_ONLINE
