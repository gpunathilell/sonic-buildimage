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
        self.index = dpu_index + 1
        self._name = f"dpu{self.index}"
        self.set_go_down_path = os.path.join(SYSTEM_BASE,
                                             f"dpu{self.index}_rst")
        self.set_pwr_path = os.path.join(SYSTEM_BASE,
                                         f"dpu{self.index}_pwr")
        self.set_pwr_f_path = os.path.join(SYSTEM_BASE,
                                           f"dpu{self.index}_pwr_force")
        self.get_dpu_rdy_path = os.path.join(EVENT_BASE,
                                             f"dpu{self.index}_ready")
        self.set_dpu_perst_en_path = os.path.join(SYSTEM_BASE,
                                                  f"dpu{self.index}_perst_en")

    def write_file(self, file_name, content_towrite):
        """Write given value to file only if file exists"""
        try:
            with DataWriter(file_name) as file_obj:
                file_obj.write(content_towrite)
        except (ValueError,
                IOError,
                PermissionError,
                FileNotFoundError) as file_write_exc:
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
                                            f"dpu{self.index}_shtdn_ready")
        try:
            get_shtdn_inotify = InotifyHelper(get_shtdn_ready_path)
            dpu_shtdn_rdy = get_shtdn_inotify.add_watch(WAIT_FOR_SHTDN, 1)
        except (FileNotFoundError, PermissionError) as inotify_exc:
            raise type(inotify_exc)(f"{self.get_name()}:{str(inotify_exc)}")
        if dpu_shtdn_rdy is None:
            print(f"{self.get_name()}: Going Down Unsuccessful")
            self.dpu_power_off(forced=True)
            self.dpu_power_on(forced=True)
            return

    def dpu_power_off(self, forced=False):
        """Per DPU Power off API"""
        print(f"{self.get_name()}: Power off forced={forced}")
        if forced:
            self.write_file(self.set_pwr_f_path, "1")
        else:
            self.write_file(self.set_go_down_path, "1")
            self.dpu_go_down()
            self.write_file(self.set_pwr_path, "1")
        print(f"{self.get_name()}: Power Off complete")

    def dpu_power_on(self, forced=False, count=4):
        """Per DPU Power on API"""
        if count < 4:
            print(f"{self.get_name()}: Failed! Retry {4-count}..")
        print(f"{self.get_name()}: Power on forced={forced}")
        if forced:
            self.write_file(self.set_pwr_f_path, "0")
        else:
            self.write_file(self.set_pwr_path, "0")
        get_rdy_inotify = InotifyHelper(self.get_dpu_rdy_path)
        dpu_rdy = get_rdy_inotify.add_watch(WAIT_FOR_DPU_READY, 1)
        if not dpu_rdy:
            if forced:
                if count > 1:
                    time.sleep(1)
                    self.dpu_power_off(forced=True)
                    self.dpu_power_on(forced=True, count=count-1)
                else:
                    print(f"{self.get_name()}: Failed Force power on! Exiting")
                    return False
            else:
                self.dpu_power_off(forced=True)
                self.dpu_power_on(forced=True)
        else:
            print(f"{self.get_name()}: Power on Successful!")
            return True

    def dpu_reboot_prep(self):
        """Per DPU Reboot API"""
        # TODO: Shutdown SONiC on DPU -> SSH Connection -> Shutdown script

    def dpu_burn_fw(self, path):
        """Per DPU Firmware Update API"""
        # TODO: Uncomment to install the bfb Image
        """if not os.path.isfile(path):
            raise FileNotFoundError(f"{self.get_name()}:File "
                                    f"{self.file_name} does not exist!")
        cmd = ["sonic_bfb_install" ,"-b" ,path,"-r","rshim"+str(self.index)]
        try:
            cmd_output = subprocess.check_output(cmd)
        except subprocess.CalledProcessError as cmd_exc:
            print("Installation failed! code",
                  cmd_exc.returncode,
                  cmd_exc.output)"""

    def dpu_pci_scan(self):
        """PCI Scan API"""
        set_pci_scan = "/sys/bus/pci/rescan"
        self.write_file(set_pci_scan, "1")

    def dpu_pci_remove(self):
        """Per DPU PCI remove API"""
        get_dpu_pci_path = os.path.join(CONFIG_BASE,
                                        f"dpu{self.index}_pci_bus_id")
        pci_string = utils.read_str_from_file(get_dpu_pci_path,
                                              raise_exception=True)
        get_pci_dev_path = "/sys/bus/pci/devices/"+pci_string+"/remove"
        self.write_file(get_pci_dev_path, "1")

    def dpu_fw_upgrade(self, path):
        """Per DPU Firmware Upgrade API"""
        print(f"{self.get_name()}: FW upgrade")
        self.dpu_burn_fw(path)
        self.dpu_reboot_prep()
        self.dpu_pci_remove()
        self.write_file(self.set_dpu_perst_en_path, "0")
        self.dpu_go_down()
        self.write_file(self.set_dpu_perst_en_path, "1")
        get_rdy_inotify = InotifyHelper(self.get_dpu_rdy_path)
        dpu_rdy = get_rdy_inotify.add_watch(WAIT_FOR_DPU_READY, 1)
        if not dpu_rdy:
            self.dpu_power_off(forced=True)
            self.dpu_power_on(forced=True)
        self.dpu_pci_scan()
        print(f"{self.get_name()}: FW upgrade complete")

    def dpu_reboot(self):
        """Per DPU Reboot API"""
        print(f"{self.get_name()}: Reboot")
        self.dpu_reboot_prep()
        self.dpu_pci_remove()
        self.write_file(self.set_go_down_path, "1")
        self.dpu_go_down()
        self.write_file(self.set_go_down_path, "0")
        get_rdy_inotify = InotifyHelper(self.get_dpu_rdy_path)
        dpu_rdy = get_rdy_inotify.add_watch(WAIT_FOR_DPU_READY, 1)
        if not dpu_rdy:
            self.dpu_power_off(forced=True)
            self.dpu_power_on(forced=True)
        self.dpu_pci_scan()
        print(f"{self.get_name()}: Reboot complete")

def call_dpu_fw_upgrade(obj, path):
    """Function to call object specific firmware update for each dpu"""
    try:
        obj.dpu_fw_upgrade(path)
    except Exception as error:
        print(f"An error occurred: {type(error).__name__} - {error}")


def call_dpu_reset(obj):
    """Function to call object specific Reset for each dpu"""
    try:
        obj.dpu_reboot()
    except Exception as error:
        print(f"An error occurred: {type(error).__name__} - {error}")


def call_dpu_power_on(obj, force):
    """Function to call object specific power on for each dpu"""
    try:
        obj.dpu_power_on(force)
    except Exception as error:
        print(f"An error occurred: {type(error).__name__} - {error}")


def call_dpu_power_off(obj, force):
    """Function to call object specific power off for each dpu"""
    try:
        obj.dpu_power_off(force)
    except Exception as error:
        print(f"An error occurred: {type(error).__name__} - {error}")