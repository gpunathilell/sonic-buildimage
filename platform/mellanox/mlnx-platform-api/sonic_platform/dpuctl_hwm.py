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

"""Class Implementation for per DPU functionality"""
import os.path
import time

try:
    from .inotify_helper import InotifyHelper
    from sonic_py_common.logger import Logger
    from sonic_platform import utils
except ImportError as e:
    raise ImportError(str(e)) from e

EVENT_BASE = "/var/run/hw-management/events/"
SYSTEM_BASE = "/var/run/hw-management/system/"
CONFIG_BASE = "/var/run/hw-management/config"
logger = Logger()

WAIT_FOR_SHTDN = 60
WAIT_FOR_DPU_READY = 60


class DataWriter():
    """Class for writing data to files"""
    def __init__(self, file_name):
        self.file_name = file_name
        self.file_obj = None
        if not os.path.isfile(self.file_name):
            raise FileNotFoundError(f"File {self.file_name} does not exist!")

    def __enter__(self):
        self.file_obj = open(self.file_name, 'w', encoding="utf-8")
        return self.file_obj

    def __exit__(self, *args):
        self.file_obj.close()


class DpuCtlPlat():
    """Class for Per DPU API Call"""
    def __init__(self, dpu_index):
        self.index = dpu_index
        self._name = f"dpu{self.index}"
        self.set_go_down_path = os.path.join(SYSTEM_BASE,
                                             f"{self._name}_rst")
        self.set_pwr_path = os.path.join(SYSTEM_BASE,
                                         f"{self._name}_pwr")
        self.set_pwr_f_path = os.path.join(SYSTEM_BASE,
                                           f"{self._name}_pwr_force")
        self.get_dpu_rdy_path = os.path.join(EVENT_BASE,
                                             f"{self._name}_ready")
        self.set_dpu_perst_en_path = os.path.join(SYSTEM_BASE,
                                                  f"{self._name}_perst_en")

    def write_file(self, file_name, content_towrite):
        """Write given value to file only if file exists"""
        try:
            with DataWriter(file_name) as file_obj:
                file_obj.write(content_towrite)
        except Exception as file_write_exc:
            logger.log_error(f'{self.get_name()}:Failed to write'
                             f'{content_towrite} to file {file_name}')
            raise type(file_write_exc)(
                f"{self.get_name()}:{str(file_write_exc)}")
        return True

    def get_name(self):
        """Return name of the DPU"""
        return self._name

    def dpu_go_down(self):
        """Per DPU going down API"""
        get_shtdn_ready_path = os.path.join(EVENT_BASE,
                                            f"{self.get_name()}_shtdn_ready")
        try:
            get_shtdn_inotify = InotifyHelper(get_shtdn_ready_path)
            dpu_shtdn_rdy = get_shtdn_inotify.add_watch(WAIT_FOR_SHTDN, 1)
        except (FileNotFoundError, PermissionError) as inotify_exc:
            raise type(inotify_exc)(f"{self.get_name()}:{str(inotify_exc)}")
        if dpu_shtdn_rdy is None:
            logger.log_info(f"{self.get_name()}: Going Down Unsuccessful")
            self.dpu_power_off(forced=True)
            return

    def dpu_power_off(self, forced=False):
        """Per DPU Power off API"""
        logger.log_info(f"{self.get_name()}: Power off forced={forced}")
        if forced:
            self.write_file(self.set_pwr_f_path, "1")
        else:
            self.write_file(self.set_go_down_path, "1")
            self.dpu_go_down()
            self.write_file(self.set_pwr_path, "1")
        logger.log_info(f"{self.get_name()}: Power Off complete")

    def _power_on_force(self, count=4):
        """Per DPU Power on with force private function"""
        if count < 4:
            logger.log_info(f"{self.get_name()}: Failed Force Power on! Retry {4-count}..")
        self.write_file(self.set_pwr_f_path, "0")
        get_rdy_inotify = InotifyHelper(self.get_dpu_rdy_path)
        dpu_rdy = get_rdy_inotify.add_watch(WAIT_FOR_DPU_READY, 1)
        if not dpu_rdy:
            if count > 1:
                time.sleep(1)
                self._power_on_force(count=count - 1)
            else:
                logger.log_info(f"{self.get_name()}: Failed Force power on! Exiting")
                return False
        logger.log_info(f"{self.get_name()}: Force Power on Successful!")
        return True

    def _power_on(self):
        """Per DPU Power on without force private function"""
        self.write_file(self.set_pwr_path, "0")
        get_rdy_inotify = InotifyHelper(self.get_dpu_rdy_path)
        dpu_rdy = get_rdy_inotify.add_watch(WAIT_FOR_DPU_READY, 1)
        if not dpu_rdy:
            logger.log_info(f"{self.get_name()}: Failed power on! Trying Force Power on")
            return self.__power_on_force()
        logger.log_info(f"{self.get_name()}:Power on Successful!")
        return True

    def dpu_power_on(self, forced=False):
        """Per DPU Power on API"""
        logger.log_info(f"{self.get_name()}: Power on with force = {forced}")
        if forced:
            return self._power_on_force()
        else:
            return self._power_on()

    def dpu_reboot(self):
        """Per DPU Reboot API"""
        logger.log_info(f"{self.get_name()}: Reboot")
        self.write_file(self.set_go_down_path, "1")
        self.dpu_go_down()
        self.write_file(self.set_go_down_path, "0")
        get_rdy_inotify = InotifyHelper(self.get_dpu_rdy_path)
        dpu_rdy = get_rdy_inotify.add_watch(WAIT_FOR_DPU_READY, 1)
        if not dpu_rdy:
            self.dpu_power_off(forced=True)
            self.dpu_power_on(forced=True)
        logger.log_info(f"{self.get_name()}: Reboot complete")
