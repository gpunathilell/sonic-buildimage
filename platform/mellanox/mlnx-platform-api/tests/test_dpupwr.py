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
from sonic_platform.dpuctl_hwm import call_dpu_power_on, call_dpu_power_off, call_dpu_reset
from sonic_platform.dpuctl_hwm import call_dpu_fw_upgrade
from sonic_platform.dpuctl_hwm import DpuCtlPlat
from .dpupwr_inputs import testData

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


class TestDpuClass:
    """Tests for dpuctl Platform API Wrapper"""
    @classmethod
    def setup_class(cls):
        """Setup function for all tests for dpuctl implementation"""
        os.environ["PATH"] += os.pathsep + scripts_path
        os.environ["MLNX_PLATFORM_API_DPUCTL_UNIT_TESTING"] = "2"

    @patch('os.path.exists', MagicMock(return_value=True))
    @patch('sonic_platform.inotify_helper.InotifyHelper.add_watch',
           MagicMock(return_value=True))
    @patch('sonic_platform.inotify_helper.InotifyHelper.__init__')
    def test_power_off(self, mock_inotify, capsys):
        """Tests for Per DPU Power Off function"""
        dpuctl_obj = obj["dpuctl_list"][0]
        mock_inotify.return_value = None
        call_dpu_power_off(dpuctl_obj, True)
        result = capsys.readouterr()
        assert result.out == testData["power_off"][0]
        call_dpu_power_off(dpuctl_obj, False)
        result = capsys.readouterr()
        assert result.out == testData["power_off"][1]
        written_data = []

        def mock_write_file(file_name, content_towrite):
            written_data.append({"file": file_name,
                                 "data": content_towrite})
            return True
        existing_wr_file = dpuctl_obj.write_file
        dpuctl_obj.write_file = mock_write_file
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
        dpuctl_obj.write_file = existing_wr_file

    @patch('os.path.exists', MagicMock(return_value=True))
    @patch('sonic_platform.inotify_helper.InotifyHelper.add_watch',
           MagicMock(return_value=True))
    @patch('sonic_platform.inotify_helper.InotifyHelper.__init__')
    def test_power_on(self, mock_inotify, capsys):
        """Tests for Per DPU Power On function"""
        dpuctl_obj = obj["dpuctl_list"][0]
        mock_inotify.return_value = None
        call_dpu_power_on(dpuctl_obj, True)
        result = capsys.readouterr()
        assert result.out == testData["power_on"][0]
        call_dpu_power_on(dpuctl_obj, False)
        result = capsys.readouterr()
        assert result.out == testData["power_on"][1]
        written_data = []

        def mock_write_file(file_name, content_towrite):
            written_data.append({"file": file_name,
                                 "data": content_towrite})
            return True
        existing_wr_file = dpuctl_obj.write_file
        dpuctl_obj.write_file = mock_write_file
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
        dpuctl_obj.write_file = existing_wr_file

    @patch('os.path.exists', MagicMock(return_value=True))
    @patch('sonic_platform.utils.read_str_from_file',
           MagicMock(return_value="dpu1_pciid"))
    @patch('sonic_platform.inotify_helper.InotifyHelper.add_watch',
           MagicMock(return_value=1))
    @patch('sonic_platform.inotify_helper.InotifyHelper.__init__')
    def test_dpu_reset(self, mock_inotify, capsys):
        """Tests for Per DPU Reset function"""
        dpuctl_obj = obj["dpuctl_list"][0]
        mock_inotify.return_value = None
        call_dpu_reset(dpuctl_obj)
        result = capsys.readouterr()
        assert result.out == testData["reset"][0]
        written_data = []

        def mock_write_file(file_name, content_towrite):
            written_data.append({"file": file_name,
                                 "data": content_towrite})
            return True
        existing_wr_file = dpuctl_obj.write_file
        dpuctl_obj.write_file = mock_write_file
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
        dpuctl_obj.write_file = existing_wr_file

    @patch('os.path.exists', MagicMock(return_value=True))
    @patch('sonic_platform.utils.read_str_from_file',
           MagicMock(return_value="dpu1_id"))
    @patch('sonic_platform.inotify_helper.InotifyHelper.add_watch',
           MagicMock(return_value=1))
    @patch('sonic_platform.inotify_helper.InotifyHelper.__init__')
    def test_dpu_fw_upgrade(self, mock_inotify, capsys):
        """Tests for Per DPU Firmware Upgrade function"""
        dpuctl_obj = obj["dpuctl_list"][0]
        mock_inotify.return_value = None
        call_dpu_fw_upgrade(dpuctl_obj, None)
        result = capsys.readouterr()
        assert result.out == testData["fw_upgrade"][0]
        written_data = []
        written_data = []

        def mock_write_file(file_name, content_towrite):
            written_data.append({"file": file_name,
                                 "data": content_towrite})
            return True
        existing_wr_file = dpuctl_obj.write_file
        dpuctl_obj.write_file = mock_write_file
        call_dpu_fw_upgrade(dpuctl_obj, None)
        print(written_data)
        assert written_data[0]["file"].endswith("remove")
        assert "1" == written_data[0]["data"]
        assert written_data[1]["file"].endswith(
                f"{dpuctl_obj.get_name()}_perst_en")
        assert "0" == written_data[1]["data"]
        assert written_data[2]["file"].endswith(
                f"{dpuctl_obj.get_name()}_perst_en")
        assert "1" == written_data[2]["data"]
        assert written_data[3]["file"].endswith("rescan")
        assert "1" == written_data[3]["data"]
        assert mock_inotify.call_args.args[0].endswith(
                f"{dpuctl_obj.get_name()}_ready")
        dpuctl_obj.write_file = existing_wr_file

    @classmethod
    def teardown_class(cls):
        """Teardown function for all tests for dpuctl implementation"""
        os.environ["MLNX_PLATFORM_API_DPUCTL_UNIT_TESTING"] = "0"
        os.environ["PATH"] = os.pathsep.join(
            os.environ["PATH"].split(os.pathsep)[:-1])
