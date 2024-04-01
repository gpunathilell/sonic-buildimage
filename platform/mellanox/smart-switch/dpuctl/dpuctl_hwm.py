"""Class Implementation for per DPU functionality"""
import os.path

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


class MyMessageWriter():
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


def write_file(file_name, content_towrite, dpu_name):
    """
    Write given value to file only if file exists
    """
    try:
        with MyMessageWriter(file_name) as file_obj:
            file_obj.write(content_towrite)
    except (ValueError, IOError, PermissionError) as file_write_exc:
        logger.log_error(f'{dpu_name}:Failed to write'
                         f'{content_towrite} to file {file_name}')
        raise type(file_write_exc)(f"{dpu_name}:{str(file_write_exc)}")
    return True


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

    def get_name(self):
        """Return name of the DPU"""
        return self._name

    def dpu_go_down(self):
        """Per DPU going down API"""
        write_file(self.set_go_down_path, "1", self.get_name())
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
        print(f"{self.get_name()}: Going Down complete")

    def dpu_power_off(self, forced=False):
        """Per DPU Power off API"""
        print(f"{self.get_name()}:Power off forced={forced}")
        if forced:
            write_file(self.set_pwr_f_path, "1", self.get_name())
        else:
            self.dpu_go_down()
            write_file(self.set_pwr_path, "1", self.get_name())
            print(f"{self.get_name()}: Power Off complete")

    def dpu_power_on(self, forced=False, count=4):
        """Per DPU Power on API"""
        if count < 4:
            print(f"{self.get_name()}:Failed! Retry {4-count}..")
        print(f"{self.get_name()}:Power on forced={forced}")
        if forced:
            write_file(self.set_pwr_f_path, "0", self.get_name())
        else:
            write_file(self.set_pwr_path, "0", self.get_name())
        get_rdy_inotify = InotifyHelper(self.get_dpu_rdy_path)
        dpu_rdy = get_rdy_inotify.add_watch(WAIT_FOR_DPU_READY, 1)
        if not dpu_rdy:
            if forced:
                if count > 1:
                    self.dpu_power_off(forced=True)
                    self.dpu_power_on(forced=True, count=count-1)
                else:
                    print(f"{self.get_name()}: Failed Force power on! Exiting")
            else:
                self.dpu_power_off(forced=True)
                self.dpu_power_on(forced=True)
        else:
            print(f"{self.get_name()}: Power on Successful!")

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

    def dpu_shutdown(self):
        """Per DPU Firmware Update API"""
        print(f"{self.get_name()}: Shut down")
        self.dpu_reboot_prep()
        self.dpu_pci_remove()
        self.dpu_go_down()
        self.dpu_power_off()

    def dpu_pci_scan(self):
        """PCI Scan API"""
        set_pci_scan = "/sys/bus/pci/rescan"
        write_file(set_pci_scan, "1", self.get_name())

    def dpu_pci_remove(self):
        """Per DPU PCI remove API"""
        get_dpu_pci_path = os.path.join(CONFIG_BASE,
                                        f"dpu{self.index}_pci_bus_id")
        pci_string = utils.read_str_from_file(get_dpu_pci_path,
                                              raise_exception=True)
        get_pci_dev_path = "/sys/bus/pci/devices/cd "+pci_string+"/remove"
        write_file(get_pci_dev_path, "1", self.get_name())

    def dpu_startup(self):
        """Per DPU Startup API"""
        print(f"{self.get_name()}: Startup")
        self.dpu_power_on()
        self.dpu_pci_scan()

    def dpu_fw_upgrade(self, path):
        """Per DPU Firmware Upgrade API"""
        print(f"{self.get_name()}: fw upgrade")
        self.dpu_burn_fw(path)
        self.dpu_reboot_prep()
        self.dpu_pci_remove()
        write_file(self.set_dpu_perst_en_path, "0", self.get_name())
        self.dpu_go_down()
        write_file(self.set_dpu_perst_en_path, "1", self.get_name())
        get_rdy_inotify = InotifyHelper(self.get_dpu_rdy_path)
        dpu_rdy = get_rdy_inotify.add_watch(WAIT_FOR_DPU_READY, 1)
        if not dpu_rdy:
            self.dpu_power_off(forced=True)
            self.dpu_power_on(forced=True)
        self.dpu_pci_scan()

    def dpu_reboot(self):
        """Per DPU Reboot API"""
        print(f"{self.get_name()}: Reboot")
        self.dpu_reboot_prep()
        self.dpu_pci_remove()
        self.dpu_go_down()
        write_file(self.set_go_down_path, "0", self.get_name())
        get_rdy_inotify = InotifyHelper(self.get_dpu_rdy_path)
        dpu_rdy = get_rdy_inotify.add_watch(WAIT_FOR_DPU_READY, 1)
        if not dpu_rdy:
            self.dpu_power_off(forced=True)
            self.dpu_power_on(forced=True)
        self.dpu_pci_scan()
