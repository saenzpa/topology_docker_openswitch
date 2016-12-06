.. toctree::

.. highlight:: sh

==========
User Guide
==========

This is an OpenSwitch node for Topology Docker.

Shells
======

This node has several shells, their details are explained below.

bash
....

This shell points to the ``bash`` shell of the node. Its prompt is set to this
value:

::
    @~~==::BASH_PROMPT::==~~@

This shell has its echo disabled also, so that commands typed in it will not
show up in the console of the user.


bash_swns
.........

This shell has all the attributes of the ``bash`` shell but all commands are
executed in the ``swns`` network namespace.

vsctl
.....

This shell has all the attributes of the ``bash`` shell but all commands are
prefixed with ``ovs-vsctl``.

vtysh
.....

This shell behaves differently depending on the availability of the ``vtysh``
``set prompt`` command.

If it is available, the shell will have its echo disabled and its prompt set to
this value:

::

    X@~~==::VTYSH_PROMPT::==~~@X

Note that this is only the prompt that will be set, contexts will still be
appearing after it, for that reason you may want to use this regular
expression if you want to match with any context that has this forced prompt:

::

    r'(\r\n)?X@~~==::VTYSH_PROMPT::==~~@X(\([-\w\s]+\))?# '

If ``set prompt`` is not available, the echo will not be disabled and the
prompt will remain in its standard value.

Be aware that in order for the node to detect the ``Segmentation fault`` error
message, the ``vytsh`` shell is started with ``stdbuf -oL vtysh``.

Before the node is destroyed at the end of its life, this shell will be exited
by sending the ``end`` and ``exit`` commands.

The Booting Process
===================

The node copies a Python script in the container that performs the following
actions:

#. Waits 30 seconds for ``/var/run/netns/swns``.
#. Waits 30 seconds for ``/etc/openswitch/hwdesc``.
#. Creates interfaces.
#. Waits 30 seconds for ``/var/run/openvswitch/db.sock``.
#. Waits 30 seconds for ``cur_hw``.
#. Waits 30 seconds for ``cur_cfg``.
#. Waits 30 seconds for ``/var/run/openvswitch/ops-switchd.pid``.
#. Waits 30 seconds for the hostname to be set to ``switch``.

For the case of ``cur_hw`` and ``cur_cfg``, their value is taken from a query
sent to ``/var/run/openswitch/db.sock``. This query has this format:

::

    'X': {
        'method': 'transact',
        'params': [
            'OpenSwitch',
            {
                'op': 'select',
                'table': 'System',
                'where': [],
                'columns': ['X']
            }
        ],
        'id': id(db_sock)
    }

The value of ``1`` is looked for in:

::

    response['result'][0]['rows'][0][X] == 1

``X`` is a placeholder for ``cur_hw`` and ``cur_cfg``.

If any of the previous waits times out, an exception of this kind will be
raised:

::

    The image did not boot correctly, ...

These errors are caused by a faulty image, the framework is just reporting
them. This errors happen *before* the very first line of test case is executed.

This node will create interfaces and will move them to ``swns`` or to
``emulns`` if the image is using the P4 simulator. Any failure in the process
of creating interfaces will be reported like this:

::

    Failed to map ports with port labels...

Depending on the error, the failing command or other information will be
displayed after that message.
