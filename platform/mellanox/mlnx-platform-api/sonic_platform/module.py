#
# Copyright (c) 2021-2024 NVIDIA CORPORATION & AFFILIATES.
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
import subprocess
import redis
import threading
from sonic_platform_base.module_base import ModuleBase
from sonic_py_common.logger import SysLogger
from .dpuctlplat import DpuCtlPlat
from ipaddress import ip_network

from . import utils
from .device_data import DeviceDataManager
from .vpd_parser import VpdParser
from .dpu_vpd_parser import DpuVpdParser
from swsscommon.swsscommon import SonicV2Connector

# Global logger class instance
logger = SysLogger()


class Module(ModuleBase):
    STATE_ACTIVATED = 1
    STATE_DEACTIVATED = 0

    STATE_DB = 6
    STATE_MODULAR_CHASSIS_SLOT_TABLE = 'MODULAR_CHASSIS_SLOT|{}'
    FIELD_SEQ_NO = 'seq_no'
    redis_client = redis.Redis(db = STATE_DB)

    def __init__(self, slot_id):
        super(Module, self).__init__()
        self.slot_id = slot_id
        self.seq_no = 0
        self.current_state = Module.STATE_DEACTIVATED
        self.lock = threading.Lock()

        self.sfp_initialized_count = 0
        self.sfp_count = 0
        self.vpd_parser = VpdParser('/run/hw-management/lc{}/eeprom/vpd_parsed')

    def get_name(self):
        return 'LINE-CARD{}'.format(self.slot_id)

    def get_model(self):
        """
        Retrieves the model number (or part number) of the device

        Returns:
            string: Model/part number of device
        """
        return self.vpd_parser.get_model()

    def get_serial(self):
        """
        Retrieves the serial number of the device

        Returns:
            string: Serial number of device
        """
        return self.vpd_parser.get_serial()

    def get_revision(self):
        """
        Retrieves the hardware revision of the device

        Returns:
            string: Revision value of device
        """
        return self.vpd_parser.get_revision()

    def get_type(self):
        return ModuleBase.MODULE_TYPE_LINE

    def get_slot(self):
        return self.slot_id

    def get_presence(self):
        return utils.read_int_from_file('/run/hw-management/system/lc{}_present'.format(self.slot_id)) == 1

    def get_position_in_parent(self):
        return self.slot_id

    def is_replaceable(self):
        return True

    def get_oper_status(self):
        if utils.read_int_from_file('/run/hw-management/system/lc{}_active'.format(self.slot_id)) == 1:
            return ModuleBase.MODULE_STATUS_ONLINE
        elif utils.read_int_from_file('/run/hw-management/system/lc{}_present'.format(self.slot_id)) == 1:
            return ModuleBase.MODULE_STATUS_PRESENT
        elif utils.read_int_from_file('/run/hw-management/system/lc{}_present'.format(self.slot_id)) == 0:
            return ModuleBase.MODULE_STATUS_EMPTY
        else:
            return ModuleBase.MODULE_STATUS_FAULT

    def _check_state(self):
        """Check Module status change:
            1. If status sysfs file value has been changed
            2. If sequence NO has been changed which means line card has been removed and inserted again.
        """
        seq_no = self._get_seq_no()
        state = utils.read_int_from_file('/run/hw-management/system/lc{}_powered'.format(self.slot_id), log_func=None)
        if state != self.current_state:
            self._re_init()
        elif seq_no != self.seq_no:
            if state == Module.STATE_ACTIVATED: # LC has been replaced, need re-initialize
                self._re_init()
        self.current_state = state
        self.seq_no = seq_no

    def _get_seq_no(self):
        try:
            seq_no = Module.redis_client.hget(Module.STATE_MODULAR_CHASSIS_SLOT_TABLE.format(self.slot_id), Module.FIELD_SEQ_NO)
            seq_no = seq_no.decode().strip()
        except Exception as e:
            seq_no = 0
        return seq_no

    def _re_init(self):
        self._thermal_list = []
        self._sfp_list = []
        self._sfp_count = 0


    ##############################################
    # THERMAL methods
    ##############################################

    def initialize_thermals(self):
        self._check_state()
        if self.current_state == Module.STATE_ACTIVATED and not self._thermal_list:
            from .thermal import initialize_linecard_thermals
            self._thermal_list = initialize_linecard_thermals(self.get_name(), self.slot_id)

    def get_num_thermals(self):
        """
        Retrieves the number of thermals available on this module

        Returns:
            An integer, the number of thermals available on this module
        """
        return DeviceDataManager.get_gearbox_count('/run/hw-management/lc{}/config'.format(self.slot_id))

    def get_all_thermals(self):
        """
        Retrieves all thermals available on this module

        Returns:
            A list of objects derived from ThermalBase representing all thermals
            available on this module
        """
        with self.lock:
            self.initialize_thermals()
            return self._thermal_list

    def get_thermal(self, index):
        """
        Retrieves thermal unit represented by (0-based) index <index>

        Args:
            index: An integer, the index (0-based) of the thermal to
            retrieve

        Returns:
            An object dervied from ThermalBase representing the specified thermal
        """
        with self.lock:
            self.initialize_thermals()
            return super(Module, self).get_thermal(index)

    ##############################################
    # SFP methods
    ##############################################
    def _create_sfp_object(self, index):
        from .sfp import SFP
        return SFP(index, slot_id=self.slot_id, linecard_port_count=self.sfp_count, lc_name=self.get_name())

    def initialize_single_sfp(self, index):
        self._check_state()
        if self.current_state == Module.STATE_ACTIVATED:
            sfp_count = self.get_num_sfps()
            if index < sfp_count:
                if not self._sfp_list:
                    self._sfp_list = [None] * sfp_count

                if not self._sfp_list[index]:
                    self._sfp_list[index] = self._create_sfp_object(index)
                    self.sfp_initialized_count += 1

    def initialize_sfps(self):
        self._check_state()
        if self.current_state == Module.STATE_ACTIVATED:
            if not self._sfp_list:
                sfp_count = self.get_num_sfps()
                for index in range(sfp_count):
                    self._sfp_list.append(self._create_sfp_object(index))
                self.sfp_initialized_count = sfp_count
            elif self.sfp_initialized_count != len(self._sfp_list):
                for index in range(len(self._sfp_list)):
                    if self._sfp_list[index] is None:
                        self._sfp_list[index] = self._create_sfp_object(index)
                self.sfp_initialized_count = len(self._sfp_list)

    def get_num_sfps(self):
        """
        Retrieves the number of sfps available on this module

        Returns:
            An integer, the number of sfps available on this module
        """
        if self.sfp_count == 0:
            self.sfp_count = DeviceDataManager.get_linecard_sfp_count(self.slot_id)
        return self.sfp_count

    def get_all_sfps(self):
        """
        Retrieves all sfps available on this module

        Returns:
            A list of objects derived from PsuBase representing all sfps
            available on this module
        """
        with self.lock:
            self.initialize_sfps()
            return self._sfp_list

    def get_sfp(self, index):
        """
        Retrieves sfp represented by (0-based) index <index>

        Args:
            index: An integer, the index (0-based) of the sfp to retrieve

        Returns:
            An object dervied from SfpBase representing the specified sfp
        """
        with self.lock:
            self.initialize_single_sfp(index)
            return super(Module, self).get_sfp(index)


class DpuModule(ModuleBase):

    def __init__(self, dpu_id):
        super(DpuModule, self).__init__()
        self.dpu_id = dpu_id
        self._name = f"DPU{self.dpu_id}"
        self._dpu_hw_name = f"dpu{self.dpu_id + 1}" # DPU names starts with dpu1 in hw
        self.dpuctl_obj = DpuCtlPlat(self._dpu_hw_name)
        self.fault_state = False
        self.dpu_vpd_parser = DpuVpdParser('/var/run/hw-management/eeprom/vpd_data', self._name)
        self.app_db = SonicV2Connector(host='127.0.0.1')
        self.app_db.connect("APPL_DB")
        self.midplane_ip = None
        self.midplane_interface = None
        self.npu_interface = None

    def get_base_mac(self):
        """
        Retrieves the base MAC address for the module

        Returns:
            A string containing the MAC address in the format
            'XX:XX:XX:XX:XX:XX'
        """
        return self.dpu_vpd_parser.get_dpu_base_mac()

    def get_model(self):
        """
        Retrieves the model number (or part number) of the device

        Returns:
            string: Model/part number of device
        """
        return self.dpu_vpd_parser.get_dpu_model()

    def get_serial(self):
        """
        Retrieves the serial number of the device

        Returns:
            string: Serial number of device
        """
        return self.dpu_vpd_parser.get_dpu_serial()

    def get_revision(self):
        """
        Retrieves the hardware revision of the device

        Returns:
            string: Revision value of device
        """
        return self.dpu_vpd_parser.get_dpu_revision()

    def reboot(self, reboot_type):
        """
        Request to reboot the module

        Args:
            reboot_type: A string, the type of reboot requested from one of the
            predefined reboot types: MODULE_REBOOT_DEFAULT, MODULE_REBOOT_CPU_COMPLEX,
            or MODULE_REBOOT_FPGA_COMPLEX

        Returns:
            bool: True if the request has been issued successfully, False if not
        """
        if reboot_type == ModuleBase.MODULE_REBOOT_DEFAULT:
            return self.dpuctl_obj.dpu_reboot()
        return False

    def set_admin_state(self, up):
        """
        Request to keep the card in administratively up/down state.
        The down state will power down the module and the status should show
        MODULE_STATUS_OFFLINE.
        The up state will take the module to MODULE_STATUS_FAULT or
        MODULE_STATUS_ONLINE states.

        Args:
            up: A boolean, True to set the admin-state to UP. False to set the
            admin-state to DOWN.

        Returns:
            bool: True if the request has been issued successfully, False if not
        """
        if up:
            power_on_success = self.dpuctl_obj.dpu_power_on()
            self.fault_state = not power_on_success
            return power_on_success
        return self.dpuctl_obj.dpu_power_off()

    def get_type(self):
        """
        Retrieves the type of the module.

        Returns:
            A string, the module-type from one of the predefined types:
            MODULE_TYPE_SUPERVISOR, MODULE_TYPE_LINE or MODULE_TYPE_FABRIC
            or MODULE_TYPE_DPU or MODULE_TYPE_SWITCH
        """
        return ModuleBase.MODULE_TYPE_DPU

    def get_name(self):
        """
        Retrieves the name of the module prefixed by SUPERVISOR, LINE-CARD,
        FABRIC-CARD, SWITCH, DPU0, DPUX

        Returns:
            A string, the module name prefixed by one of MODULE_TYPE_SUPERVISOR,
            MODULE_TYPE_LINE or MODULE_TYPE_FABRIC or MODULE_TYPE_DPU or
            MODULE_TYPE_SWITCH and followed by a 0-based index.

            Ex. A Chassis having 1 supervisor, 4 line-cards and 6 fabric-cards
            can provide names SUPERVISOR0, LINE-CARD0 to LINE-CARD3,
            FABRIC-CARD0 to FABRIC-CARD5.
            A SmartSwitch having 4 DPUs and 1 Switch can provide names DPU0 to
            DPU3 and SWITCH
        """
        return self._name

    def get_description(self):
        """
        Retrieves the platform vendor's product description of the module

        Returns:
            A string, providing the vendor's product description of the module.
        """
        return "NVIDIA BlueField-3 DPU"

    def get_oper_status(self):
        if self.fault_state:
            return ModuleBase.MODULE_STATUS_FAULT

        dataplane_state = self._is_dataplane_online()
        midplane_state = self.is_midplane_reachable()

        if dataplane_state and midplane_state:
            return ModuleBase.MODULE_STATUS_CONTROLPLANE_ONLINE

        if dataplane_state:
            return ModuleBase.MODULE_STATUS_DATAPLANE_ONLINE

        if midplane_state:
            return ModuleBase.MODULE_STATUS_MIDPLANE_ONLINE

        if self._is_online():
            return ModuleBase.MODULE_STATUS_ONLINE

        return ModuleBase.MODULE_STATUS_OFFLINE

    ##############################################
    # SmartSwitch methods
    ##############################################

    def get_dpu_id(self):
        """
        Retrieves the DPU ID. Returns None for non-smartswitch chassis.
        Returns:
            An integer, indicating the DPU ID. DPU0 returns 1, DPUX returns X+1
            Returns '0' on switch module
        """
        return self.dpu_id

    def get_reboot_cause(self):
        """
        Retrieves the cause of the previous reboot of the DPU module
        Returns:
            A tuple (string, string) where the first element is a string
            containing the cause of the previous reboot. This string must
            be one of the predefined strings in this class. If the first
            string is "REBOOT_CAUSE_HARDWARE_OTHER", the second string can be
            used to pass a description of the reboot cause.
            Some more causes are appended to the existing list to handle other
            modules such as DPUs.
            Ex: REBOOT_CAUSE_POWER_LOSS, REBOOT_CAUSE_HOST_RESET_DPU,
            REBOOT_CAUSE_HOST_POWERCYCLED_DPU, REBOOT_CAUSE_SW_THERMAL,
            REBOOT_CAUSE_DPU_SELF_REBOOT
        """
        self.reboot_cause_map = {
            f'/run/hw-management/system/dpu{self._dpu_hw_name}/system/reset_from_main_board':
                (ModuleBase.REBOOT_CAUSE_HOST_RESET_DPU, ''),
            f'/run/hw-management/system/dpu{self._dpu_hw_name}/system/reset_dpu_thermal':
                (ModuleBase.REBOOT_CAUSE_SW_THERMAL, ''),
            f'/run/hw-management/system/dpu{self._dpu_hw_name}/system/reset_aux_pwr_or_reload':
                (ModuleBase.REBOOT_CAUSE_POWER_LOSS, ''),
            f'/run/hw-management/system/dpu{self._dpu_hw_name}/system/reset_pwr_off':
                (ModuleBase.REBOOT_CAUSE_DPU_SELF_REBOOT, ''),
            f'/run/hw-management/system/dpu{self._dpu_hw_name}/system/tpm_rst':
                (ModuleBase.REBOOT_CAUSE_HARDWARE_OTHER, 'Reset by the TPM module'),
            f'/run/hw-management/system/dpu{self._dpu_hw_name}/system/perst_rst':
                (ModuleBase.REBOOT_CAUSE_HARDWARE_OTHER, 'PERST# signal to ASIC'),
            f'/run/hw-management/system/dpu{self._dpu_hw_name}/system/phy_rst':
                (ModuleBase.REBOOT_CAUSE_HARDWARE_OTHER, 'Phy reset'),
            f'/run/hw-management/system/dpu{self._dpu_hw_name}/system/usbphy_rst':
                (ModuleBase.REBOOT_CAUSE_HARDWARE_OTHER, 'USB Phy reset'),
        }
        for f, rd in self.reboot_cause_map.items():
            if utils.read_int_from_file(f) == 1:
                return rd
        return ModuleBase.REBOOT_CAUSE_NON_HARDWARE, ''

    def get_midplane_ip(self):
        """
        Retrieves the midplane IP-address of the module in a modular chassis
        When called from the Supervisor, the module could represent the
        line-card and return the midplane IP-address of the line-card.
        When called from the line-card, the module will represent the
        Supervisor and return its midplane IP-address.
        When called from the DPU, returns the midplane IP-address of the dpu-card.
        When called from the Switch returns the midplane IP-address of Switch.
        Returns:
            A string, the IP-address of the module reachable over the midplane
        """
        if not self.midplane_ip:
            midplane_data = DeviceDataManager.get_platform_midplane_network()
            network_cidr = midplane_data['bridge_address']
            ip_network_cidr = ip_network(network_cidr, strict=False)
            self.midplane_ip = str(ip_network_cidr[self.dpu_id])
        return self.midplane_ip

    def is_midplane_reachable(self):
        """
        Retrieves the reachability status of the module from the Supervisor or
        of the Supervisor from the module via the midplane of the modular chassis
        Returns:
            A bool value, should return True if module is reachable via midplane
        """
        if not self._is_midplane_up():
            return False

        command = ['ping', '-c', '1', '-W', '1', self.get_midplane_ip()]
        try:
            return subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0
        except Exception:
            logger.log_error(f"Failed to check midplane reachability for {self.get_name()}!")
            return False

    def _is_midplane_up(self):
        if not self.midplane_interface:
            platform_dpus_data = DeviceDataManager.get_platform_dpus_data()
            print(platform_dpus_data)
            self.midplane_interface = platform_dpus_data[self.get_name().lower()]["midplane_interface"]
        return utils.read_str_from_file(f'/sys/class/net/{self.midplane_interface}/operstate') == "up"

    def _is_dataplane_online(self):
        """Check if the dataplane interface is online by querying APPL_DB
        """
        if not self.npu_interface:
            platform_dpus_data = DeviceDataManager.get_platform_dpus_data()
            npu_dpu_mapping = platform_dpus_data[self.get_name().lower()]["interface"]
            self.npu_interface = list(npu_dpu_mapping.keys())[0]
        oper_status = self.app_db.get("APPL_DB", "PORT_TABLE:" + self.npu_interface, "oper_status")
        return oper_status == "up":

    def _is_online(self):
        return utils.read_int_from_file(f'/run/hw-management/events/{self._dpu_hw_name}_ready') == 1
