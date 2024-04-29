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

import os
from sonic_py_common.logger import Logger

from . import utils

logger = Logger()
SN_VPD_FIELD = "SN_VPD_FIELD"
PN_VPD_FIELD = "PN_VPD_FIELD"
REV_VPD_FIELD = "REV_VPD_FIELD"
MFR_VPD_FIELD = "MFR_NAME"


class VpdParser:
    def __init__(self, file_path, smart_switch_data=False, dpu_id=-1):
        self.vpd_data = {}
        self.vpd_file = file_path
        self.vpd_file_last_mtime = None
        self.smart_switch_data = smart_switch_data
        self.dpu_id = dpu_id

    def _get_data(self):
        if not os.path.exists(self.vpd_file):
            self.vpd_data = {}
            return False

        try:
            mtime = os.stat(self.vpd_file).st_mtime
            if mtime != self.vpd_file_last_mtime:
                self.vpd_file_last_mtime = mtime
                if self.smart_switch_data:
                    self.vpd_data = utils.read_key_value_file_first_delim(self.vpd_file)
                else:
                    self.vpd_data = utils.read_key_value_file(self.vpd_file)
            return True
        except Exception as e:
            self.vpd_data = {}
            return False

    def get_model(self):
        """
        Retrieves the model number (or part number) of the device

        Returns:
            string: Model/part number of device
        """
        if self._get_data() and PN_VPD_FIELD not in self.vpd_data:
            logger.log_error("Fail to read model number: No key {} in VPD {}".format(PN_VPD_FIELD, self.vpd_file))
            return 'N/A'
        return self.vpd_data.get(PN_VPD_FIELD, 'N/A')

    def get_serial(self):
        """
        Retrieves the serial number of the device

        Returns:
            string: Serial number of device
        """
        if self._get_data() and SN_VPD_FIELD not in self.vpd_data:
            logger.log_error("Fail to read serial number: No key {} in VPD {}".format(SN_VPD_FIELD, self.vpd_file))
            return 'N/A'
        return self.vpd_data.get(SN_VPD_FIELD, 'N/A')

    def get_revision(self):
        """
        Retrieves the hardware revision of the device

        Returns:
            string: Revision value of device
        """
        if self._get_data() and REV_VPD_FIELD not in self.vpd_data:
            logger.log_error("Fail to read revision: No key {} in VPD {}".format(REV_VPD_FIELD, self.vpd_file))
            return 'N/A'
        return self.vpd_data.get(REV_VPD_FIELD, 'N/A')

    def get_entry_value(self, key):
        """
        Retrieves an vpd entry of the device

        Returns:
            string: Vpd entry value of device
        """
        if self._get_data() and key not in self.vpd_data:
            logger.log_warning("Fail to read vpd info: No key {} in VPD {}".format(key, self.vpd_file))
            return 'N/A'
        return self.vpd_data.get(key, 'N/A')

    def get_dpu_data(self, key=None):
        if not self.smart_switch_data or self.dpu_id == -1:
            logger.log_warning("Fail to read vpd info: smart_switch_data and dpu_id is not initialized, key={} in VPD = {}".format(key, self.vpd_file))
            return 'N/A'
        if key is not None:
            return self.get_entry_value(key)
        return {key: value for key, value in self.vpd_data.items() if key.startswith(f"DPU{self.dpu_id}")}

    def get_dpu_base_mac(self):
        return self.get_dpu_data(f"DPU{self.dpu_id}_BASE_MAC")

    def get_dpu_system_eeprom_info(self):
        return self.get_dpu_data()
