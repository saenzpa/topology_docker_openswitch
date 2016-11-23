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

from os.path import exists, basename, splitext, join
from shutil import copytree, Error, rmtree
from logging import warning
from datetime import datetime

from topology_docker_openswitch.openswitch import log_commands


def pytest_runtest_teardown(item):
    """
    Pytest hook to get node information after the test executed.

    This creates a folder with the name of the test case, copies the folders
    defined in the shared_dir_mount attribute of each openswitch container
    and the /var/log/messages file inside.

    FIXME: document the item argument
    """
    test_suite = splitext(basename(item.parent.name))[0]
    path_name = '/tmp/topology/docker/{}_{}_{}'.format(
        test_suite, item.name, datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
    )

    # Being extra-prudent here
    if exists(path_name):
        rmtree(path_name)

    if 'topology' not in item.funcargs:
        from topology_docker_openswitch.openswitch import LOG_PATHS

        for log_path in LOG_PATHS:
            try:
                destination = join(path_name, basename(log_path))
                try:
                    rmtree(destination)
                except:
                    pass
                copytree(log_path, destination)
                rmtree(path_name)
            except Error as err:
                errors = err.args[0]
                for error in errors:
                    src, dest, msg = error
                    warning(
                        'Unable to copy file {}, Error {}'.format(
                            src, msg
                        )
                    )
        return

    topology = item.funcargs['topology']

    if topology.engine != 'docker':
        return

    logs_path = '/var/log/messages'

    for node in topology.nodes:
        node_obj = topology.get(node)

        if node_obj.metadata.get('type', None) != 'openswitch':
            return

        shared_dir = node_obj.shared_dir

        try:
            commands = ['cat {}'.format(logs_path)]
            log_commands(
                commands, join(node_obj.shared_dir_mount, 'container_logs'),
                node_obj._docker_exec, prefix=r'sh -c "', suffix=r'"'
            )
        except:
            warning(
                'Unable to get {} from node {}.'.format(
                    logs_path, node_obj.identifier
                )
            )

        bash_shell = node_obj.get_shell('bash')

        try:
            core_path = '/var/diagnostics/coredump'

            bash_shell.send_command(
                'ls -1 {}/core.* 2>/dev/null'.format(core_path), silent=True
            )

            core_files = bash_shell.get_response(silent=True).splitlines()

            for core_file in core_files:
                bash_shell.send_command(
                    'cp {core_path}/{core_file} /tmp'.format(**locals()),
                    silent=True
                )
        except:
            warning(
                'Unable to get coredumps from node {}.'.format(
                    node_obj.identifier
                )
            )

        try:
            copytree(shared_dir, join(path_name, basename(shared_dir)))
            rmtree(shared_dir)
        except Error as err:
            errors = err.args[0]
            for error in errors:
                src, dest, msg = error
                warning(
                    'Unable to copy file {}, Error {}'.format(
                        src, msg
                    )
                )
