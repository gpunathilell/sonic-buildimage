#
# Copyright (c) 2020-2021 NVIDIA CORPORATION & AFFILIATES.
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
# ssd update tool

MLNX_SONIC_BFB_INSTALL = sonic_bfb_installer
$(MLNX_SONIC_BFB_INSTALL)_PATH = $(PLATFORM_PATH)/

MLNX_BFB_INSTALL = bfb-install
$(MLNX_BFB_INSTALL)_PATH = $(PLATFORM_PATH)/

MLNX_BFB_FILES = $(MLNX_BFB_INSTALL) $(MLNX_SONIC_BFB_INSTALL) 


SONIC_COPY_FILES += $(MLNX_BFB_FILES)


MLNX_FILES += $(MLNX_BFB_FILES)

export MLNX_SONIC_BFB_INSTALL
export MLNX_BFB_INSTALL
