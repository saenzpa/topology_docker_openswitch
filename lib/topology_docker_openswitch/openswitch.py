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
Custom Topology Docker Node for OpenSwitch.

    http://openswitch.net/
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

from json import loads
from subprocess import check_output, CalledProcessError
from platform import system, linux_distribution
from logging import StreamHandler, getLogger, INFO, Formatter
from sys import stdout

from topology_docker.node import DockerNode
from topology_docker.shell import DockerShell, DockerBashShell

# When a failure happens during boot time, logs and other information is
# collected to help with the debugging. The path of this collection is to be
# stored here at module level to be able to import it in the pytest teardown
# hook later. Non-failing containers will append their log paths here also.
LOG_PATHS = []

SETUP_SCRIPT = """\
import logging
from sys import argv
from time import sleep
from os.path import exists, split
from json import dumps, loads
from shlex import split as shsplit
from subprocess import check_call, check_output, call, CalledProcessError
from socket import AF_UNIX, SOCK_STREAM, socket, gethostname

import re
import yaml

config_timeout = 1200
ops_switchd_active_timeout = 60
swns_netns = '/var/run/netns/swns'
emulns_netns = '/var/run/netns/emulns'
hwdesc_dir = '/etc/openswitch/hwdesc'
db_sock = '/var/run/openvswitch/db.sock'
switchd_pid = '/var/run/openvswitch/ops-switchd.pid'
query_cur_hw = {
    'method': 'transact',
    'params': [
        'OpenSwitch',
        {
            'op': 'select',
            'table': 'System',
            'where': [],
            'columns': ['cur_hw']
        }
    ],
    'id': id(db_sock)
}
query_cur_cfg = {
    'method': 'transact',
    'params': [
        'OpenSwitch',
        {
            'op': 'select',
            'table': 'System',
            'where': [],
            'columns': ['cur_cfg']
        }
    ],
    'id': id(db_sock)
}
sock = None


def create_interfaces():
    # Read ports from hardware description
    with open('{}/ports.yaml'.format(hwdesc_dir), 'r') as fd:
        ports_hwdesc = yaml.load(fd)
    hwports = [str(p['name']) for p in ports_hwdesc['ports']]

    netns = check_output("ls /var/run/netns", shell=True)
    # Get list of already created ports
    not_in_netns = check_output(shsplit(
        'ls /sys/class/net/'
    )).split()
    if "emulns" not in netns:
        in_netns = check_output(shsplit(
            'ip netns exec swns ls /sys/class/net/'
        )).split()
    else:
        in_netns = check_output(shsplit(
            'ip netns exec emulns ls /sys/class/net/'
        )).split()
    logging.info(
            '  - Not in swns/emulns {not_in_netns} '.format(
                **locals()
            )
        )
    logging.info(
            '  - In swns/emulns {in_netns} '.format(
                **locals()
            )
        )

    create_cmd_tpl = 'ip tuntap add dev {hwport} mode tap'
    netns_cmd_tpl_swns = 'ip link set {hwport} netns swns'
    netns_fp_cmd_tpl_swns = ('ip link set {hwport} netns swns')
    netns_cmd_tpl_emulns = ('ip netns exec swns ip link set {hwport} '
                            'netns emulns')

    netns_fp_cmd_tpl_emulns = ('ip link set {hwport} netns emulns')
    rename_int = ('ip link set {portlbl} name {hwport}')
    ns_exec = 'ip netns exec emulns '

    # Save port mapping information
    mapping_ports = {}

    # Map the port with the labels
    for portlbl in not_in_netns:
        logging.info(
            '  - Port {portlbl} found'.format(
                **locals()
            )
        )
        if portlbl in ['lo', 'oobm', 'eth0', 'bonding_masters']:
            continue
        hwport = hwports.pop(0)
        mapping_ports[portlbl] = hwport
        logging.info(
            '  - Port {portlbl} moved to swns/emulns netns as {hwport}.'
            .format(**locals())
        )
        try:
            check_call(shsplit(rename_int.format(**locals())))
            if 'emulns' not in netns:
                check_call(shsplit(netns_fp_cmd_tpl_swns
                           .format(hwport=hwport)))
            else:
                check_call(shsplit(netns_fp_cmd_tpl_emulns
                           .format(hwport=hwport)))
                check_call('{ns_exec} ip link set dev {hwport} up'
                           .format(**locals()), shell=True)
                for i in range(0, config_timeout):
                    link_state = check_output(
                        '{ns_exec} ip link show {hwport}'
                        .format(**locals()), shell=True)
                    if "UP" in link_state:
                        break;
                    else:
                        sleep(0.1)
                else:
                    raise Exception('Emulns interface did not came up...')

                out = check_output(
                    '{ns_exec} echo port_add {hwport} '
                    ' {port} | {ns_exec} '
                    '/usr/bin/bm_tools/runtime_CLI.py --json '
                    '/usr/share/ovs_p4_plugin/switch_bmv2.json '
                    '--thrift-port 10001'.format(ns_exec=ns_exec,
                                                 hwport=hwport,
                                                 port=str(int(hwport) - 1)),
                    shell=True
                )
                logging.info('BM port creation...')
                logging.info(out)
                re_str = r''''\s*Control utility for runtime P4 table \
manipulation\s*\nRuntimeCmd:\s*\nRuntimeCmd:\s*$'''  #noqa

                if re.findall(re_str, out, re.MULTILINE) is None:
                    raise Exception('Control utility for runtime P4 table '
                                    'failed...')
        except Exception as error:
            raise Exception(
                'Failed to map ports with port labels: {}'.format(
                    error.message
                )
            )

    # Writting mapping to file
    shared_dir_tmp = split(__file__)[0]
    with open('{}/port_mapping.json'.format(shared_dir_tmp), 'w') as json_file:
        json_file.write(dumps(mapping_ports))

    for hwport in hwports:
        if hwport in in_netns:
            logging.info('  - Port {} already present.'.format(hwport))
            continue

        logging.info('  - Port {} created.'.format(hwport))
        try:
            if "emulns" not in netns:
                check_call(shsplit(create_cmd_tpl.format(hwport=hwport)))
        except:
            raise Exception('Failed to create tuntap')

        try:
            if 'emulns' not in netns:
                check_call(shsplit(netns_cmd_tpl_swns.format(hwport=hwport)))
        except:
            raise Exception('Failed to move port to swns/emulns netns')
    check_call(shsplit('touch /tmp/ops-virt-ports-ready'))
    logging.info('  - Ports readiness notified to the image')

def cur_hw_is_set():
    global sock
    if sock is None:
        sock = socket(AF_UNIX, SOCK_STREAM)
        sock.connect(db_sock)
    sock.send(dumps(query_cur_hw))
    response = loads(sock.recv(4096))
    try:
        return response['result'][0]['rows'][0]['cur_hw'] == 1
    except IndexError:
        return 0

def cur_cfg_is_set():
    global sock
    if sock is None:
        sock = socket(AF_UNIX, SOCK_STREAM)
        sock.connect(db_sock)
    sock.send(dumps(query_cur_cfg))
    response = loads(sock.recv(4096))
    try:
        return response['result'][0]['rows'][0]['cur_cfg'] == 1
    except IndexError:
        return 0

def ops_switchd_is_active():
    is_active = call(["systemctl", "is-active", "switchd.service"])
    return is_active == 0

def main():

    if '-d' in argv:
        logging.basicConfig(level=logging.DEBUG)

    logging.info('Waiting for swns netns...')
    for i in range(0, config_timeout):
        if not exists(swns_netns):
            sleep(0.1)
        else:
            break
    else:
        raise Exception('Timed out while waiting for swns/emulns.')

    logging.info('Waiting for hwdesc directory...')
    for i in range(0, config_timeout):
        if not exists(hwdesc_dir):
            sleep(0.1)
        else:
            break
    else:
        raise Exception('Timed out while waiting for hwdesc directory.')

    logging.info('Creating interfaces...')
    create_interfaces()

    logging.info('Waiting for DB socket...')
    for i in range(0, config_timeout):
        if not exists(db_sock):
            sleep(0.1)
        else:
            break
    else:
        raise Exception('Timed out while waiting for DB socket.')

    logging.info('Waiting for cur_hw...')
    for i in range(0, config_timeout):
        if not cur_hw_is_set():
            sleep(0.1)
        else:
            break
    else:
        raise Exception('Timed out while waiting for cur_hw.')

    logging.info('Waiting for cur_cfg...')
    for i in range(0, config_timeout):
        if not cur_cfg_is_set():
            sleep(0.1)
        else:
            break
    else:
        raise Exception('Timed out while waiting for cur_cfg.')

    logging.info('Waiting for switchd pid...')
    for i in range(0, config_timeout):
        if not exists(switchd_pid):
            sleep(0.1)
        else:
            break
    else:
        raise Exception('Timed out while waiting for switchd pid.')

    logging.info('Waiting for ops-switchd to become active...')
    for i in range(0, ops_switchd_active_timeout):
        if not ops_switchd_is_active():
            sleep(1)
        else:
            break
    else:
        raise Exception('Timed out while waiting for ops-switchd '
                        'to become active.')

    logging.info('Wait for final hostname...')
    for i in range(0, config_timeout):
        if gethostname() != 'switch':
            sleep(0.1)
        else:
            break
    else:
        raise Exception('Timed out while waiting for final hostname.')

    logging.info('Checking restd service status...')
    output = ''
    try:
        output = check_output(
            'systemctl status restd', shell=True
        )
    except CalledProcessError as e:
        pass
    if 'Active: active' not in output:
        try:
            logging.info('Starting restd daemon...')
            check_output('systemctl start restd', shell=True)
            logging.info('Checking restd service started...')
            for i in range(0, config_timeout):
                output = ''
                output = check_output(
                    'systemctl status restd', shell=True
                )
                if 'Active: active' not in output:
                    sleep(0.1)
                else:
                    break
            else:
                raise Exception("Failed to start restd service")
        except CalledProcessError as e:
            raise Exception(
                'Failed to start restd: {}'.format(e.output)
            )
        except Exception as error:
            raise Exception (
                error
            )

if __name__ == '__main__':
    main()
"""

LOG = getLogger(__name__)
LOG_HDLR = StreamHandler(stream=stdout)
LOG_HDLR.setFormatter(Formatter('%(asctime)s %(message)s'))
LOG_HDLR.setLevel(INFO)
LOG.addHandler(LOG_HDLR)
LOG.setLevel(INFO)


def log_commands(
    commands, location, function, escape=True,
    prefix=None, suffix=None, **kwargs
):
    if prefix is None:
        prefix = ''
    if suffix is None:
        suffix = ''

    for command in commands:
        log_path = ' >> {} 2>&1'.format(location)
        args = [
            r'{prefix}echo \"Output of:'
            r' {command}{log_path}\"{log_path}{suffix}'.format(
                prefix=prefix, command=command,
                log_path=log_path, suffix=suffix
            ),
            r'{}{}{}{}'.format(
                prefix, command, log_path, suffix
            ),
            r'{}echo \"\"{}{}'.format(prefix, log_path, suffix)
        ]

        for arg in args:
            try:
                if not escape:
                    arg = arg.replace('\\', '')
                function(arg, **kwargs)

            except CalledProcessError as error:
                LOG.warning(
                    '{} failed with error {}.'.format(
                        command, error.returncode
                    )
                )


class OpenSwitchNode(DockerNode):
    """
    Custom OpenSwitch node for the Topology Docker platform engine.
    This custom node loads an OpenSwitch image and has vtysh as default
    shell (in addition to bash).
    See :class:`topology_docker.node.DockerNode`.
    """

    def __init__(
            self, identifier,
            image='topology/ops:latest', binds=None,
            environment={'container': 'docker'},
            **kwargs):

        # Add binded directories
        container_binds = [
            '/dev/log:/dev/log',
            '/sys/fs/cgroup:/sys/fs/cgroup:ro'
        ]
        if binds is not None:
            container_binds.append(binds)

        super(OpenSwitchNode, self).__init__(
            identifier, image=image, command='/sbin/init',
            binds=';'.join(container_binds), hostname='switch',
            network_mode='bridge', **kwargs
        )

        # FIXME: Remove this attribute to merge with version > 1.6.0
        self.shared_dir_mount = '/tmp'

        # Add vtysh (default) shell
        # FIXME: Create a subclass to handle better the particularities of
        # vtysh, like prompt setup etc.
        self._register_shell(
            'vtysh',
            DockerShell(
                self.container_id, 'vtysh',
                '(^|\n)switch(\([\-a-zA-Z0-9]*\))?#'
            )
        )

        # Add bash shells
        initial_prompt = '(^|\n).*[#$] '

        self._register_shell(
            'bash',
            DockerBashShell(
                self.container_id, 'bash',
                initial_prompt=initial_prompt
            )
        )
        self._register_shell(
            'bash_swns',
            DockerBashShell(
                self.container_id, 'ip netns exec swns bash',
                initial_prompt=initial_prompt
            )
        )
        self._register_shell(
            'vsctl',
            DockerBashShell(
                self.container_id, 'bash',
                initial_prompt=initial_prompt,
                prefix='ovs-vsctl ', timeout=60
            )
        )

    def notify_post_build(self):
        """
        Get notified that the post build stage of the topology build was
        reached.

        See :meth:`DockerNode.notify_post_build` for more information.
        """
        super(OpenSwitchNode, self).notify_post_build()
        self._setup_system()

    def _setup_system(self):
        """
        Setup the OpenSwitch image for testing.

        #. Wait for daemons to converge.
        #. Assign an interface to each port label.
        #. Create remaining interfaces.
        """

        # Write and execute setup script
        setup_script = '{}/openswitch_setup.py'.format(self.shared_dir)
        with open(setup_script, 'w') as fd:
            fd.write(SETUP_SCRIPT)

        try:
            self._docker_exec(
                'python {}/openswitch_setup.py -d'.format(
                    self.shared_dir_mount
                )
            )
        except Exception as e:
            global FAIL_LOG_PATH
            lines_to_dump = 100

            platforms_log_location = {
                'Ubuntu': 'cat /var/log/upstart/docker.log',
                'CentOS Linux': 'grep docker /var/log/daemon.log',
                # FIXME: find the right values for the next dictionary keys:
                # 'boot2docker': 'cat /var/log/docker.log',
                # 'debian': 'cat /var/log/daemon.log',
                # 'fedora': 'journalctl -u docker.service',
                # 'red hat': 'grep docker /var/log/messages',
                # 'opensuse': 'journalctl -u docker.service'
            }

            # Here, we find the command to dump the last "lines_to_dump" lines
            # of the docker log file in the logs. The location of the docker
            # log file depends on the Linux distribution. These locations are
            # defined the in "platforms_log_location" dictionary.

            operating_system = system()

            if operating_system != 'Linux':
                LOG.warning(
                    'Operating system is not Linux but {}.'.format(
                        operating_system
                    )
                )
                return

            linux_distro = linux_distribution()[0]

            if linux_distro not in platforms_log_location.keys():
                LOG.warning(
                    'Unknown Linux distribution {}.'.format(
                        linux_distro
                    )
                )

            docker_log_command = '{} | tail -n {}'.format(
                platforms_log_location[linux_distro], lines_to_dump
            )

            container_commands = [
                'ovs-vsctl list Daemon',
                'coredumpctl gdb',
                'ps -aef',
                'systemctl status',
                'systemctl --state=failed --all',
                'ovsdb-client dump',
                'systemctl status switchd -n 10000 -l',
                'cat /var/log/messages'
            ]

            execution_machine_commands = [
                'tail -n 2000 /var/log/syslog',
                'docker ps -a',
                docker_log_command
            ]

            log_commands(
                container_commands,
                '{}/container_logs'.format(self.shared_dir_mount),
                self._docker_exec,
                prefix=r'sh -c "',
                suffix=r'"'
            )
            log_commands(
                execution_machine_commands,
                '{}/execution_machine_logs'.format(self.shared_dir),
                check_output,
                escape=False,
                shell=True
            )
            LOG_PATHS.append(self.shared_dir)

            raise e
        # Read back port mapping
        port_mapping = '{}/port_mapping.json'.format(self.shared_dir)
        with open(port_mapping, 'r') as fd:
            mappings = loads(fd.read())

        LOG_PATHS.append(self.shared_dir)

        if hasattr(self, 'ports'):
            self.ports.update(mappings)
            return
        self.ports = mappings

    def set_port_state(self, portlbl, state):
        """
        Set the given port label to the given state.

        See :meth:`DockerNode.set_port_state` for more information.
        """
        iface = self.ports[portlbl]
        state = 'up' if state else 'down'

        not_in_netns = self._docker_exec('ls /sys/class/net/').split()
        prefix = '' if iface in not_in_netns else 'ip netns exec swns'

        command = '{prefix} ip link set dev {iface} {state}'.format(**locals())
        self._docker_exec(command)


__all__ = ['OpenSwitchNode']
