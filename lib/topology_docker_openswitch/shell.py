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
OpenSwitch shell module
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

from topology_docker.shell import DockerShell

from topology_openswitch.vtysh import (
    BASH_FORCED_PROMPT,
    VTYSH_FORCED_PROMPT,
    VTYSH_STANDARD_PROMPT,
    VtyshShellMixin,
    ValgrindShellMixin,
)


class OpenSwitchVtyshShell(DockerShell, VtyshShellMixin):
    """
    OpenSwitch ``vtysh`` shell

    This shell handles the particularities of the ``vtysh`` shell of an
    OpenSwitch node. It is actually a shell that connects first to ``bash`` and
    from the ``bash`` shell it then opens a ``vtysh`` shell.

    The actual process that this shell follows depends on the image of the
    OpenSwitch node. Newer images support the ``vtysh`` ``set prompt`` command,
    older images do not. This command allows the user to change the vtysh
    prompt to any value without other side effects (like the hostname command
    has).

    #. A connection to the ``bash`` shell of the node is done.
    #. The ``bash`` prompt is set to ``@~~==::BASH_PROMPT::==~~@``.
    #. A ``vtysh`` shell is opened with ``stdbuf -oL vtysh``.
    #. The ``vtysh`` ``set prompt X@~~==::VTYSH_PROMPT::==~~@X`` command is
       executed to set the ``vtysh`` forced prompt.

    If the next prompt received matches the ``vtysh`` forced prompt, this
    process is followed:

    #. The ``vtysh`` shell is exited back to the ``bash`` shell by sending
       ``exit``.
    #. The echo of the ``bash`` shell is disabled with ``stty -echo``. This
       will also disable the echo of the ``vtysh`` shell that will be started
       from the ``bash`` shell.
    #. A ``vtysh`` shell will be started with ``stdbuf -oL vtysh``.
    #. The ``vtysh`` ``set prompt X@~~==::VTYSH_PROMPT::==~~@X`` command is
       executed.
    #. The shell prompt is set to the forced ``vtysh`` prompt.
    #. In this case, the shell will not try to remove the echo of the ``vtysh``
       commands because they should not appear since the echo is disabled.

    If the next prompt received does not match the ``vtysh`` forced prompt,
    this process is followed:

    #. The shell is configured to try to remove the echo of the ``vtysh``
       commands by looking for them in the command output.
    #. The shell prompt is set to the standard ``vtysh`` prompt.

    Once the container is to be destroyed in the normal clean up of nodes, the
    ``vtysh`` shell is exited to the ``bash`` one by sending the ``end``
    command followed by the ``exit`` command.

    :param str container: identifier of the container that holds this shell
    """

    def __init__(self, container):
        # The parameter try_filter_echo is disabled by default here to handle
        # images that support the vtysh "set prompt" command and will have its
        # echo disabled since it extends from DockeBashShell. For other
        # situations where this is not supported, the self._try_filter_echo
        # attribute is disabled afterwards by altering it directly.
        # The prompt value passed here is the one that will match with an
        # OpenSwitch bash shell initial prompt.
        super(OpenSwitchVtyshShell, self).__init__(
            container, 'bash', '(^|\n).*[#$] ', try_filter_echo=False
        )

    def _setup_shell(self, connection=None):
        """
        Get the shell ready to handle ``vtysh`` particularities.

        These particularities are the handling of segmentation fault errors
        and forced or standard ``vtysh`` prompts.

        See :meth:`PExpectShell._setup_shell` for more information.
        """

        spawn = self._get_connection(connection)
        # Since user, password or initial_command are not being used, this is
        # the first expect done in the connection. The value of self._prompt at
        # this moment is the initial prompt of an OpenSwitch bash shell prompt.
        spawn.expect(self._prompt)

        # The bash prompt is set to a forced value for vtysh shells that
        # support prompt setting and for the ones that do not.
        spawn.sendline('export PS1={}'.format(BASH_FORCED_PROMPT))
        spawn.expect(BASH_FORCED_PROMPT)

        def join_prompt(prompt):
            return '{}|{}'.format(BASH_FORCED_PROMPT, prompt)

        if self._determine_set_prompt():
            # If this image supports "set prompt", then exit back to bash to
            # set the bash shell without echo.
            spawn.sendline('exit')
            spawn.expect(BASH_FORCED_PROMPT)

            # This disables the echo in the bash and in the subsequent vtysh
            # shell too.
            spawn.sendline('stty -echo')
            spawn.expect(BASH_FORCED_PROMPT)

            # Go into the vtysh shell again. Exiting vtysh after calling "set
            # prompt" successfully disables the vtysh shell prompt to its
            # standard value, so it is necessary to call it again.
            self._determine_set_prompt()

            # From now on the shell _prompt attribute is set to the defined
            # vtysh forced prompt.
            self._prompt = '|'.join([BASH_FORCED_PROMPT, VTYSH_FORCED_PROMPT])

        else:
            # If the image does not support "set prompt", then enable the
            # filtering of echo by setting the corresponding attribute to True.
            # WARNING: Using a private attribute here.
            self._try_filter_echo = True

            # From now on the shell _prompt attribute is set to the defined
            # vtysh standard prompt.
            self._prompt = '|'.join(
                [BASH_FORCED_PROMPT, VTYSH_STANDARD_PROMPT]
            )

        # This sendline is used here just because a _setup_shell must end in an
        # send/sendline call since it is followed by a call to expect in the
        # connect method.
        spawn.sendline('')

    def send_command(
        self, command, matches=None, newline=True, timeout=None,
        connection=None, silent=False
    ):
        # This parent method performs the connection to the shell and the set
        # up of a bash prompt to an unique value.
        match_index = super(OpenSwitchVtyshShell, self).send_command(
            command, matches=matches, newline=newline, timeout=timeout,
            connection=connection, silent=silent
        )

        # This will raise a proper exception if a crash has been found.
        self._handle_crash(connection)

        return match_index


class OpenSwitchValgrindShell(ValgrindShellMixin, OpenSwitchVtyshShell):
    def _setup_shell(self, connection=None):
        """
        Get the shell ready to handle ``valgrind`` particularities.

        These particularities are the handling of segmentation fault errors
        and forced or standard ``valgrind`` prompts.

        See :meth:`PExpectShell._setup_shell` for more information.
        """

        spawn = self._get_connection(connection)
        # Since user, password or initial_command are not being used, this is
        # the first expect done in the connection. The value of self._prompt at
        # this moment is the initial prompt of an OpenSwitch bash shell prompt.
        spawn.expect(self._prompt)

        # The bash prompt is set to a forced value for valgrind shells that
        # support prompt setting and for the ones that do not.
        spawn.sendline('export PS1={}'.format(BASH_FORCED_PROMPT))
        spawn.expect(BASH_FORCED_PROMPT)

        def join_prompt(prompt):
            return '{}|{}'.format(BASH_FORCED_PROMPT, prompt)

        if self._determine_set_prompt():
            # If this image supports "set prompt", then exit back to bash to
            # set the bash shell without echo.
            spawn.sendline('exit')
            spawn.expect(BASH_FORCED_PROMPT)

            # This disables the echo in the bash and in the subsequent valgrind
            # shell too.
            spawn.sendline('stty -echo')
            spawn.expect(BASH_FORCED_PROMPT)

            # Go into the valgrind shell again. Exiting valgrind after calling "set
            # prompt" successfully disables the valgrind shell prompt to its
            # standard value, so it is necessary to call it again.
            self._determine_set_prompt()

            # From now on the shell _prompt attribute is set to the defined
            # valgrind forced prompt.
            self._prompt = '|'.join([BASH_FORCED_PROMPT, VTYSH_FORCED_PROMPT])

        else:
            # If the image does not support "set prompt", then enable the
            # filtering of echo by setting the corresponding attribute to True.
            # WARNING: Using a private attribute here.
            self._try_filter_echo = True

            # From now on the shell _prompt attribute is set to the defined
            # valgrind standard prompt.
            self._prompt = '|'.join(
                [BASH_FORCED_PROMPT, VTYSH_STANDARD_PROMPT]
            )

        # This sendline is used here just because a _setup_shell must end in an
        # send/sendline call since it is followed by a call to expect in the
        # connect method.
        spawn.sendline('')

    def send_command(
        self, command, matches=None, newline=True, timeout=None,
        connection=None, silent=False
    ):
        # This parent method performs the connection to the shell and the set
        # up of a bash prompt to an unique value.
        match_index = super(OpenSwitchValgrindShell, self).send_command(
            command, matches=matches, newline=newline, timeout=timeout,
            connection=connection, silent=silent
        )

        # This will raise a proper exception if a crash has been found.
        self._handle_crash(connection)

        return match_index


__all__ = ['OpenSwitchVtyshShell',
           'OpenSwitchValgrindShell']
