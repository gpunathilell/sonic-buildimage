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

"""dpuctl Tests Implementation"""
import os
import sys
import pytest

from click.testing import CliRunner
from sonic_platform.dpuctl_hwm import DpuCtlPlat
import sonic_platform
import mock

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
        dpuctl_list.append(DpuCtlPlat(dpu_name))
    context = {
        "dpuctl_list": dpuctl_list,
    }
    return context


obj = create_dpu_list()


class TestDpuClass:
    """Tests for dpuctl Platform API Wrapper"""
    @classmethod
    def setup_class(cls):
        """Setup function for all tests for dpuctl implementation"""
        os.environ["PATH"] += os.pathsep + scripts_path
        os.environ["MLNX_PLATFORM_API_DPUCTL_UNIT_TESTING"] = "2"

    @patch('os.path.exists', MagicMock(return_value=True))
    @patch('sonic_platform.inotify_helper.InotifyHelper.add_watch')
    @patch('sonic_platform.inotify_helper.InotifyHelper.__init__')
    def test_power_off(self, mock_inotify, mock_add_watch):
        """Tests for Per DPU Power Off function"""
        dpuctl_obj = obj["dpuctl_list"][0]
        mock_inotify.return_value = None
        mock_add_watch.return_value = True
        with pytest.raises(FileNotFoundError, match="/var/run/hw-management"
                           "/system/dpu1_pwr_force does not exist!"):
            dpuctl_obj.dpu_power_off(True)
        with pytest.raises(FileNotFoundError, match="/var/run/hw-management"
                           "/system/dpu1_rst does not exist!"):
            dpuctl_obj.dpu_power_off(False)
        written_data = []

        def mock_write_file(file_name, content_towrite):
            written_data.append({"file": file_name,
                                 "data": content_towrite})
            return True
        existing_wr_file = dpuctl_obj.write_file
        dpuctl_obj.write_file = mock_write_file
        assert dpuctl_obj.dpu_power_off(True)
        assert written_data[0]["file"].endswith(
            f"{dpuctl_obj.get_name()}_pwr_force")
        assert "1" == written_data[0]["data"]
        written_data = []
        assert dpuctl_obj.dpu_power_off(False)
        assert mock_inotify.call_args.args[0].endswith(
            f"{dpuctl_obj.get_name()}_shtdn_ready")
        assert written_data[0]["file"].endswith(f"{dpuctl_obj.get_name()}_rst")
        assert "1" == written_data[0]["data"]
        assert written_data[1]["file"].endswith(f"{dpuctl_obj.get_name()}_pwr")
        assert "1" == written_data[1]["data"]
        written_data = []
        mock_add_watch.return_value = None
        assert dpuctl_obj.dpu_power_off(False)
        assert mock_inotify.call_args.args[0].endswith(
            f"{dpuctl_obj.get_name()}_shtdn_ready")
        assert written_data[0]["file"].endswith(f"{dpuctl_obj.get_name()}_rst")
        assert "1" == written_data[0]["data"]
        assert written_data[1]["file"].endswith(f"{dpuctl_obj.get_name()}_pwr_force")
        assert "1" == written_data[1]["data"]
        dpuctl_obj.write_file = existing_wr_file

    @patch('os.path.exists', MagicMock(return_value=True))
    @patch('sonic_platform.inotify_helper.InotifyHelper.add_watch')
    @patch('sonic_platform.inotify_helper.InotifyHelper.__init__')
    def test_power_on(self, mock_inotify, mock_add_watch):
        """Tests for Per DPU Power On function"""
        dpuctl_obj = obj["dpuctl_list"][0]
        mock_inotify.return_value = None
        mock_add_watch.return_value = True
        with pytest.raises(FileNotFoundError, match="/var/run/hw-management"
                           "/system/dpu1_pwr_force does not exist!"):
            dpuctl_obj.dpu_power_on(True)
        with pytest.raises(FileNotFoundError, match="/var/run/hw-management"
                           "/system/dpu1_pwr does not exist"):
            dpuctl_obj.dpu_power_on(False)
        written_data = []

        def mock_write_file(file_name, content_towrite):
            written_data.append({"file": file_name,
                                 "data": content_towrite})
            return True
        existing_wr_file = dpuctl_obj.write_file
        dpuctl_obj.write_file = mock_write_file
        assert dpuctl_obj.dpu_power_on(True)
        assert mock_inotify.call_args.args[0].endswith(
            f"{dpuctl_obj.get_name()}_ready")
        assert written_data[0]["file"].endswith(
            f"{dpuctl_obj.get_name()}_pwr_force")
        assert "0" == written_data[0]["data"]
        written_data = []
        assert dpuctl_obj.dpu_power_on(False)
        assert written_data[0]["file"].endswith(f"{dpuctl_obj.get_name()}_pwr")
        assert "0" == written_data[0]["data"]
        written_data = []
        mock_add_watch.return_value = None
        print("test2")
        assert not dpuctl_obj.dpu_power_on(False)
        print(written_data)
        assert len(written_data) == 5
        print(written_data)
        assert written_data[0]["file"].endswith(f"{dpuctl_obj.get_name()}_pwr")
        assert "0" == written_data[0]["data"]
        assert written_data[1]["file"].endswith(
            f"{dpuctl_obj.get_name()}_pwr_force")
        assert "0" == written_data[1]["data"]
        assert written_data[2]["file"].endswith(
            f"{dpuctl_obj.get_name()}_pwr_force")
        assert "0" == written_data[2]["data"]
        assert written_data[3]["file"].endswith(
            f"{dpuctl_obj.get_name()}_pwr_force")
        assert "0" == written_data[3]["data"]
        assert written_data[4]["file"].endswith(
            f"{dpuctl_obj.get_name()}_pwr_force")
        assert "0" == written_data[4]["data"]
        dpuctl_obj.write_file = existing_wr_file

    @patch('os.path.exists', MagicMock(return_value=True))
    @patch('sonic_platform.inotify_helper.InotifyHelper.add_watch')
    @patch('sonic_platform.inotify_helper.InotifyHelper.__init__')
    def test_dpu_reset(self, mock_inotify,mock_add_watch):
        """Tests for Per DPU Reset function"""
        dpuctl_obj = obj["dpuctl_list"][0]
        mock_inotify.return_value = None
        mock_add_watch.return_value = True
        with pytest.raises(FileNotFoundError, match="/var/run/hw-management"
                           "/system/dpu1_rst does not exist!"):
            dpuctl_obj.dpu_reboot()
        written_data = []

        def mock_write_file(file_name, content_towrite):
            written_data.append({"file": file_name,
                                 "data": content_towrite})
            return True
        existing_wr_file = dpuctl_obj.write_file
        dpuctl_obj.write_file = mock_write_file
        assert dpuctl_obj.dpu_reboot()
        assert written_data[0]["file"].endswith(f"{dpuctl_obj.get_name()}_rst")
        assert "1" == written_data[0]["data"]
        assert written_data[1]["file"].endswith(f"{dpuctl_obj.get_name()}_rst")
        assert "0" == written_data[1]["data"]
        assert mock_inotify.call_args.args[0].endswith(
            f"{dpuctl_obj.get_name()}_ready")
        mock_add_watch.return_value = None 
        written_data = []
        assert not dpuctl_obj.dpu_reboot()
        assert len(written_data) == 7
        assert written_data[0]["file"].endswith(f"{dpuctl_obj.get_name()}_rst")
        assert "1" == written_data[0]["data"]
        assert written_data[1]["file"].endswith(f"{dpuctl_obj.get_name()}_pwr_force")
        assert "1" == written_data[1]["data"]
        assert written_data[2]["file"].endswith(f"{dpuctl_obj.get_name()}_rst")
        assert "0" == written_data[2]["data"]
        assert written_data[3]["file"].endswith(f"{dpuctl_obj.get_name()}_pwr_force")
        assert "0" == written_data[3]["data"]
        dpuctl_obj.write_file = existing_wr_file

    @classmethod
    def teardown_class(cls):
        """Teardown function for all tests for dpuctl implementation"""
        os.environ["MLNX_PLATFORM_API_DPUCTL_UNIT_TESTING"] = "0"
        os.environ["PATH"] = os.pathsep.join(
            os.environ["PATH"].split(os.pathsep)[:-1])
