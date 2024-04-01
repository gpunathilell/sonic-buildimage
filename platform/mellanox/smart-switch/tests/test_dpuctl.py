"""dpuctl Tests Implementation"""
import os
import sys
import pytest

from click.testing import CliRunner
from dpuctl.main import call_dpu_power_on, call_dpu_power_off, call_dpu_reset
from dpuctl.main import call_dpu_shutdown, call_dpu_fw_upgrade
from dpuctl.main import call_dpu_startup
import dpuctl.main as dpuctl_main
from dpuctl import dpuctl_hwm
from dpuctl.dpuctl_hwm import DpuCtlPlat
from dpuctl_inputs.dpuctl_test_inputs import testData

if sys.version_info.major == 3:
    from unittest.mock import MagicMock, patch

test_path = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.dirname(test_path)
sys.path.insert(0, modules_path)
scripts_path = os.path.join(modules_path, "scripts")


def create_dpu_list():
    """Create dpu object list for Function calls"""
    existing_dpu_list = ['dpu1', 'dpu2', 'dpu3', 'dpu4']
    dpuctl_list = []
    for dpu_name in existing_dpu_list:
        index = int(dpu_name[-1])-1
        dpuctl_list.append(DpuCtlPlat(index))
    context = {
        "dpuctl_list": dpuctl_list,
    }
    return context


obj = create_dpu_list()


def dpuctl_command_exec(exec_cmd, command_name):
    """General Command Execution and return value
        validation function for all the APIs"""
    test_data_checks = testData[command_name]
    runner = CliRunner()
    assertion_checks = test_data_checks['AssertionError']
    for args in assertion_checks['arg_list']:
        with pytest.raises(AssertionError, match=r"Invalid Arguments"):
            runner.invoke(exec_cmd, args, catch_exceptions=False, obj=obj)
    result_checks = test_data_checks['Returncheck']
    for index_value in range(len(result_checks['arg_list'])):
        args = result_checks['arg_list'][index_value]
        return_code = result_checks['rc'][index_value]
        return_message = result_checks['return_message'][index_value]
        result = runner.invoke(exec_cmd, args, catch_exceptions=False, obj=obj)
        assert result.exit_code == return_code
        print(f"Command = {command_name}")
        print(f"Return message = {return_message}")
        print(f"result.output = {result.output}")
        assert return_message == result.output


class Testdpuctl:
    """Tests for dpuctl Platform API Wrapper"""
    @classmethod
    def setup_class(cls):
        """Setup function for all tests for dpuctl implementation"""
        os.environ["PATH"] += os.pathsep + scripts_path
        os.environ["MLNX_PLATFORM_API_DPUCTL_UNIT_TESTING"] = "2"

    @patch('multiprocessing.Process.start', MagicMock(return_value=True))
    @patch('multiprocessing.Process.join', MagicMock(return_value=True))
    def test_dpuctl_power_off(self):
        """Tests for dpuctl click Implementation for Power Off API"""
        exec_cmd = dpuctl_main.dpuctl_power_off
        dpuctl_command_exec(exec_cmd, "PW_OFF")

    @patch('multiprocessing.Process.start', MagicMock(return_value=True))
    @patch('multiprocessing.Process.join', MagicMock(return_value=True))
    def test_dpuctl_power_on(self):
        """Tests for dpuctl click Implementation for Power On API"""
        exec_cmd = dpuctl_main.dpuctl_power_on
        dpuctl_command_exec(exec_cmd, "PW_ON")

    @patch('multiprocessing.Process.start', MagicMock(return_value=True))
    @patch('multiprocessing.Process.join', MagicMock(return_value=True))
    def test_dpuctl_reset(self):
        """Tests for dpuctl click Implementation for Reset API"""
        exec_cmd = dpuctl_main.dpuctl_reset
        dpuctl_command_exec(exec_cmd, "RST")

    @patch('multiprocessing.Process.start', MagicMock(return_value=True))
    @patch('multiprocessing.Process.join', MagicMock(return_value=True))
    def test_dpuctl_fw_upgrade(self):
        """Tests for dpuctl click Implementation for Firmware Upgrade API"""
        exec_cmd = dpuctl_main.dpuctl_fw_upgrade
        dpuctl_command_exec(exec_cmd, "FW_UPG")

    @patch('multiprocessing.Process.start', MagicMock(return_value=True))
    @patch('multiprocessing.Process.join', MagicMock(return_value=True))
    def test_dpuctl_startup(self):
        """Tests for dpuctl click Implementation for Startup API"""
        exec_cmd = dpuctl_main.dpuctl_startup
        dpuctl_command_exec(exec_cmd, "STRTUP")

    @patch('multiprocessing.Process.start', MagicMock(return_value=True))
    @patch('multiprocessing.Process.join', MagicMock(return_value=True))
    def test_dpuctl_shutdown(self):
        """Tests for dpuctl click Implementation for Shutdown API"""
        exec_cmd = dpuctl_main.dpuctl_shutdown
        dpuctl_command_exec(exec_cmd, "SHTDN")

    @patch('os.path.exists', MagicMock(return_value=True))
    @patch('dpuctl.inotify_helper.InotifyHelper.add_watch',
           MagicMock(return_value=True))
    @patch('dpuctl.inotify_helper.InotifyHelper.__init__')
    def test_power_off(self, mock_inotify):
        """Tests for Per DPU Power Off function"""
        dpuctl_obj = obj["dpuctl_list"][0]
        mock_inotify.return_value = None
        with pytest.raises(FileNotFoundError, match=r"dpu1_pwr_force"):
            call_dpu_power_off(dpuctl_obj, True)
        with pytest.raises(FileNotFoundError, match=r"dpu1_rst"):
            call_dpu_power_off(dpuctl_obj, False)
        written_data = []

        def mock_write_file(file_name, content_towrite, dpu_name):
            written_data.append({"file": file_name,
                                 "data": content_towrite,
                                 "dpu_name": dpu_name})
            return True
        existing_wr_file = dpuctl_hwm.write_file
        dpuctl_hwm.write_file = mock_write_file
        call_dpu_power_off(dpuctl_obj, True)
        assert written_data[0]["file"].endswith(
                f"{dpuctl_obj.get_name()}_pwr_force")
        assert "1" == written_data[0]["data"]
        written_data = []
        call_dpu_power_off(dpuctl_obj, False)
        assert mock_inotify.call_args.args[0].endswith(
                f"{dpuctl_obj.get_name()}_shtdn_ready")
        assert written_data[0]["file"].endswith(f"{dpuctl_obj.get_name()}_rst")
        assert "1" == written_data[0]["data"]
        assert written_data[1]["file"].endswith(f"{dpuctl_obj.get_name()}_pwr")
        assert "1" == written_data[1]["data"]
        dpuctl_hwm.write_file = existing_wr_file

    @patch('os.path.exists', MagicMock(return_value=True))
    @patch('dpuctl.inotify_helper.InotifyHelper.add_watch',
           MagicMock(return_value=True))
    @patch('dpuctl.inotify_helper.InotifyHelper.__init__')
    def test_power_on(self, mock_inotify):
        """Tests for Per DPU Power On function"""
        dpuctl_obj = obj["dpuctl_list"][0]
        mock_inotify.return_value = None
        with pytest.raises(FileNotFoundError, match=r"dpu1_pwr_force"):
            call_dpu_power_on(dpuctl_obj, True)
        with pytest.raises(FileNotFoundError, match=r"dpu1_pwr"):
            call_dpu_power_on(dpuctl_obj, False)
        written_data = []

        def mock_write_file(file_name, content_towrite, dpu_name):
            written_data.append({"file": file_name,
                                 "data": content_towrite,
                                 "dpu_name": dpu_name})
            return True
        existing_wr_file = dpuctl_hwm.write_file
        dpuctl_hwm.write_file = mock_write_file
        call_dpu_power_on(dpuctl_obj, True)
        assert mock_inotify.call_args.args[0].endswith(
                f"{dpuctl_obj.get_name()}_ready")
        assert written_data[0]["file"].endswith(
                f"{dpuctl_obj.get_name()}_pwr_force")
        assert "0" == written_data[0]["data"]
        written_data = []
        call_dpu_power_on(dpuctl_obj, False)
        assert written_data[0]["file"].endswith(f"{dpuctl_obj.get_name()}_pwr")
        assert "0" == written_data[0]["data"]
        dpuctl_hwm.write_file = existing_wr_file

    @patch('os.path.exists', MagicMock(return_value=True))
    @patch('sonic_platform.utils.read_str_from_file',
           MagicMock(return_value="dpu1_pciid"))
    @patch('dpuctl.inotify_helper.InotifyHelper.add_watch',
           MagicMock(return_value=1))
    @patch('dpuctl.inotify_helper.InotifyHelper.__init__')
    def test_dpu_reset(self, mock_inotify):
        """Tests for Per DPU Reset function"""
        dpuctl_obj = obj["dpuctl_list"][0]
        mock_inotify.return_value = None
        with pytest.raises(FileNotFoundError, match=r"dpu1_pciid"):
            call_dpu_reset(dpuctl_obj)
        written_data = []

        def mock_write_file(file_name, content_towrite, dpu_name):
            written_data.append({"file": file_name,
                                 "data": content_towrite,
                                 "dpu_name": dpu_name})
            return True
        existing_wr_file = dpuctl_hwm.write_file
        dpuctl_hwm.write_file = mock_write_file
        call_dpu_reset(dpuctl_obj)
        assert written_data[0]["file"].endswith("remove")
        assert "1" == written_data[0]["data"]
        assert written_data[1]["file"].endswith(f"{dpuctl_obj.get_name()}_rst")
        assert "1" == written_data[1]["data"]
        assert written_data[2]["file"].endswith(f"{dpuctl_obj.get_name()}_rst")
        assert "0" == written_data[2]["data"]
        assert written_data[3]["file"].endswith("rescan")
        assert "1" == written_data[3]["data"]
        assert mock_inotify.call_args.args[0].endswith(
                f"{dpuctl_obj.get_name()}_ready")
        dpuctl_hwm.write_file = existing_wr_file

    @patch('os.path.exists', MagicMock(return_value=True))
    @patch('sonic_platform.utils.read_str_from_file',
           MagicMock(return_value="dpu1_id"))
    @patch('dpuctl.inotify_helper.InotifyHelper.add_watch',
           MagicMock(return_value=1))
    @patch('dpuctl.inotify_helper.InotifyHelper.__init__')
    def test_dpu_fw_upgrade(self, mock_inotify):
        """Tests for Per DPU Firmware Upgrade function"""
        dpuctl_obj = obj["dpuctl_list"][0]
        mock_inotify.return_value = None
        with pytest.raises(FileNotFoundError, match=r"dpu1_id"):
            call_dpu_fw_upgrade(dpuctl_obj, None)
        written_data = []

        def mock_write_file(file_name, content_towrite, dpu_name):
            written_data.append({"file": file_name,
                                 "data": content_towrite,
                                 "dpu_name": dpu_name})
            return True
        existing_wr_file = dpuctl_hwm.write_file
        dpuctl_hwm.write_file = mock_write_file
        call_dpu_fw_upgrade(dpuctl_obj, None)
        print(written_data)
        assert written_data[0]["file"].endswith("remove")
        assert "1" == written_data[0]["data"]
        assert written_data[1]["file"].endswith(
                f"{dpuctl_obj.get_name()}_perst_en")
        assert "0" == written_data[1]["data"]
        assert written_data[2]["file"].endswith(f"{dpuctl_obj.get_name()}_rst")
        assert "1" == written_data[2]["data"]
        assert written_data[3]["file"].endswith(
                f"{dpuctl_obj.get_name()}_perst_en")
        assert "1" == written_data[3]["data"]
        assert written_data[4]["file"].endswith("rescan")
        assert "1" == written_data[4]["data"]
        assert mock_inotify.call_args.args[0].endswith(
                f"{dpuctl_obj.get_name()}_ready")
        dpuctl_hwm.write_file = existing_wr_file

    @patch('os.path.exists', MagicMock(return_value=True))
    @patch('sonic_platform.utils.read_str_from_file',
           MagicMock(return_value="dpu1_id"))
    @patch('dpuctl.inotify_helper.InotifyHelper.add_watch',
           MagicMock(return_value=1))
    @patch('dpuctl.inotify_helper.InotifyHelper.__init__')
    def test_dpu_shutdown(self, mock_inotify):
        """Tests for Per DPU Shutdown function"""
        dpuctl_obj = obj["dpuctl_list"][0]
        mock_inotify.return_value = None
        written_data = []

        def mock_write_file(file_name, content_towrite, dpu_name):
            written_data.append({"file": file_name,
                                 "data": content_towrite,
                                 "dpu_name": dpu_name})
            return True
        existing_wr_file = dpuctl_hwm.write_file
        dpuctl_hwm.write_file = mock_write_file
        call_dpu_shutdown(dpuctl_obj)
        print(written_data)
        assert written_data[0]["file"].endswith("remove")
        assert "1" == written_data[0]["data"]
        assert written_data[1]["file"].endswith(
                f"{dpuctl_obj.get_name()}_rst")
        assert "1" == written_data[1]["data"]
        assert mock_inotify.call_args.args[0].endswith(
                f"{dpuctl_obj.get_name()}_shtdn_ready")
        assert written_data[2]["file"].endswith(
                f"{dpuctl_obj.get_name()}_rst")
        assert "1" == written_data[2]["data"]
        assert written_data[3]["file"].endswith(
                f"{dpuctl_obj.get_name()}_pwr")
        assert "1" == written_data[3]["data"]
        dpuctl_hwm.write_file = existing_wr_file

    @patch('os.path.exists', MagicMock(return_value=True))
    @patch('sonic_platform.utils.read_str_from_file',
           MagicMock(return_value="dpu1_id"))
    @patch('dpuctl.inotify_helper.InotifyHelper.add_watch',
           MagicMock(return_value=1))
    @patch('dpuctl.inotify_helper.InotifyHelper.__init__')
    def test_dpu_startup(self, mock_inotify):
        """Tests for Per DPU Startup function"""
        dpuctl_obj = obj["dpuctl_list"][0]
        mock_inotify.return_value = None
        written_data = []

        def mock_write_file(file_name, content_towrite, dpu_name):
            written_data.append({"file": file_name,
                                 "data": content_towrite,
                                 "dpu_name": dpu_name})
            return True
        existing_wr_file = dpuctl_hwm.write_file
        dpuctl_hwm.write_file = mock_write_file
        call_dpu_startup(dpuctl_obj)
        print(written_data)
        assert written_data[0]["file"].endswith(
                f"{dpuctl_obj.get_name()}_pwr")
        assert "0" == written_data[0]["data"]
        assert mock_inotify.call_args.args[0].endswith(
                f"{dpuctl_obj.get_name()}_ready")
        assert written_data[1]["file"].endswith("rescan")
        assert "1" == written_data[1]["data"]
        dpuctl_hwm.write_file = existing_wr_file

    @classmethod
    def teardown_class(cls):
        """Teardown function for all tests for dpuctl implementation"""
        os.environ["MLNX_PLATFORM_API_DPUCTL_UNIT_TESTING"] = "0"
        os.environ["PATH"] = os.pathsep.join(
            os.environ["PATH"].split(os.pathsep)[:-1])
