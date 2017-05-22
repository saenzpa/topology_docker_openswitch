# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2016 Hewlett Packard Enterprise Development LP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""
Test suite for module topology_docker_openswitch.
"""

from unittest.mock import patch

from pytest import raises
from ipdb import set_trace

from topology_docker_openswitch.shell import OpenSwitchVtyshShell
from topology_openswitch.vtysh import UnknownError, SegmentationFaultError


@patch.object(OpenSwitchVtyshShell, '_get_connect_command')
def test_unknown_error(mock_get_connect_command):
    mock_get_connect_command.configure_mock(
        **{'return_value': 'test-shell behavior_unknown.py'}
    )

    shell = OpenSwitchVtyshShell('123456')

    with raises(UnknownError):
        set_trace()
        shell.send_command('some_command')


@patch.object(OpenSwitchVtyshShell, '_get_connect_command')
def test_segmentation_fault_error(mock_get_connect_command):
    mock_get_connect_command.configure_mock(
        **{'return_value': 'test-shell behavior_segmentation_fault.py'}
    )

    shell = OpenSwitchVtyshShell('123456')

    with raises(SegmentationFaultError):
        shell.send_command('some_command')
