===================================
openswitch node for topology_docker
===================================

A Topology OpenSwitch Node for topology_docker.

Changelog
=========


1.1.5 (2018-03-06)
------------------
- Merge pull request #31 from saenzpa/package_fix. [Pablo Saenz]

  fix: dev: Add openswitch_setup script to package.


1.1.4 (2017-06-01)
------------------
- Merge pull request #30 from saenzpa/dev_log_removal. [Diego Hurtado]

  Remove switch container volume mount dev/log
- Remove switch container volume mount dev/log. [Sergio Barahona]

  This mount was used to gather logs from containers and log them in the
  execution machine, it was an old practice from first topology days and
  is not required anymore.

  The removal is mainly because there are some vtysh commands that extract
  data from local log files, so the logs need to be on the container instead
  of the execution machine.


1.1.3 (2017-02-21)
------------------
- Merge branch 'herjosep-p4_string_ifnames' [Diego Antonio Hurtado
  Pimentel]


1.1.1 (2017-02-12)
------------------
- Merge pull request #28 from saenzpa/no_rest. [Diego Hurtado]

  No rest
- Revert "fix: dev: Refactoring to remove race conditions." [Diego
  Antonio Hurtado Pimentel]

  This reverts commit 53bf52b8693adfb3a2a5b664a30186b6a881b63c.
- Merge pull request #27 from saenzpa/P4refactor. [Pablo Saenz]

  fix: dev: Refactoring to remove race conditions.
- Merge pull request #26 from saenzpa/remove_rest. [Diego Hurtado]

  fix: dev: Parametrize setup script path.


1.1.0 (2017-01-19)
------------------
- Merge pull request #25 from saenzpa/operator_prompt. [Diego Hurtado]

  Operator prompt


1.0.1 (2016-12-06)
------------------

Fix
~~~
- Documenting exit from vtysh. [Diego Antonio Hurtado Pimentel]


1.0.0 (2016-11-23)
------------------
- Merge pull request #24 from saenzpa/no_echo. [Diego Hurtado]

  fix: dev: Removing shell echo.
- Merge pull request #23 from saenzpa/environment_fix. [Pablo Saenz]

  fix: dev: Passing 'container' env variable.
- Merge pull request #22 from saenzpa/hpe_sync_with_logs. [Diego
  Hurtado]

  chg: dev: Setting environment container to docker.
- Merge pull request #21 from saenzpa/script_mod. [Pablo Saenz]

  fix: dev: Increasing config timeout.
- Merge pull request #20 from saenzpa/register_shell. [Diego Hurtado]

  chg: dev: Using _register_shell.
- Merge pull request #19 from saenzpa/coredumps. [Pablo Saenz]

  chg: dev: Collecting docker coredumps on teardown and adding checks for p4 simulator
- Merge pull request #17 from saenzpa/p4switch. [Pablo Saenz]

  chg: dev: adding support for p4simulator images


0.1.0 (2016-08-12)
------------------

Changes
~~~~~~~
- The binds attribute can now be injected and extended by users. [Carlos
  Miguel Jenkins Perez]

Fix
~~~
- Fixed bug in initial prompt matching causing bash based shells to
  timeout. [Carlos Miguel Jenkins Perez]

Other
~~~~~
- Merge pull request #16 from saenzpa/restd_start. [Diego Hurtado]

  Restd start
- Fixing restd validation status and service start. [fonsecamau]
- Merge pull request #15 from saenzpa/file_exist_fix. [Pablo Saenz]

  fix: dev: Adding handler for existing files.
- Merge pull request #14 from saenzpa/bringup_checks. [Pablo Saenz]

  chg: dev: Modifying boot time checks
- Merge pull request #13 from saenzpa/improved_logging. [Diego Hurtado]

  chg: dev: Improving logging.
- Merge pull request #11 from saenzpa/ops_switchd_active_timeout. [Pablo
  Saenz]

  chg: dev: Increase ops-switchd active timeout
- Merge pull request #9 from saenzpa/switchd_active. [Pablo Saenz]

  chg: dev: Add check for ops-switchd to be active
- Merge pull request #8 from baraserg/master. [Pablo Saenz]

  Use safe method of querying dictionary
- Merge pull request #11 from baraserg/master. [Diego Hurtado]

  fix: dev: Change static path to shared_dir attribute
- Merge pull request #7 from saenzpa/log_messages. [Pablo Saenz]

  Log messages
- Merge pull request #6 from baraserg/master. [Pablo Saenz]

  Merge log plugin
- Merge pull request #5 from saenzpa/master_sync. [Pablo Saenz]

  Master sync
- Merge pull request #4 from HPENetworking/master. [Pablo Saenz]

  pulling from master
- Merge pull request #9 from fonsecamau/master. [Carlos Jenkins]

  chg: dev: Adding/modifying logging feature on process bring-up
- Merge pull request #8 from fonsecamau/master. [Carlos Jenkins]

  new: dev: Adding more logging and exception handling
- Merge pull request #24 from HPENetworking/new_shell_api_migration.
  [David Diaz Barquero]

  chg: dev: Migrated all nodes shells to new Topology shell API.
- Merge pull request #23 from HPENetworking/new_binds_attribute. [Carlos
  Jenkins]

  chg: usr: The binds attribute can now be injected and extended by users.
- Merge pull request #20 from HPENetworking/ddompe-patch-1. [Diego
  Hurtado]

  Improvements during initialization
- Fix bugs during initialization. [Diego Dompe]

  - Handle support for sync the port readiness with the newer openswitch images
  - Delay waiting for the cur_cfg, and handle  the case where the cfg is not ready yet better.
- Merge pull request #19 from agustin-meneses-fuentes/master. [Carlos
  Jenkins]

  fix: dev: Add bonding_masters to ip link set exceptions
- Merge pull request #11 from walintonc/master. [Carlos Jenkins]

  new: usr: Add support to specifying the hostname for a node.
- Add support to specifying hostname for create_container. [Walinton
  Cambronero]

  - This allows that nodes can specify the hostname of choice
  - In the openswitch node, the default hostname is 'switch'
  - Clarify that tag must be specified in image param
- Merge pull request #2 from fonsecamau/fix_cut_output. [Carlos Jenkins]

  fix: dev: Make vtysh shell regular expression for prompt more specific.
- Merge pull request #19 from hpe-networking/fix_cut_output. [Carlos
  Miguel Jenkins Perez]

  fix: dev: Output gets confused with switch prompt
- Merge pull request #17 from hpe-networking/ops_oobm. [Carlos Miguel
  Jenkins Perez]

  chg: dev: Avoid moving new oobm interface to swns namespace
- Merge pull request #15 from hpe-networking/after_autopull. [David Diaz
  Barquero]

  Refactored code, fixed minor issues and code quality.
- Merge pull request #8 from hpe-networking/docker_tmp. [David Diaz
  Barquero]

  Mapping port to port labels for openswitch in topology
- Merge pull request #4 from hpe-networking/send_command_to_docker_exec.
  [David Diaz Barquero]

  chg: dev: Refactored all send_commands to docker_exec to avoid using pexpect.
- Merge pull request #3 from hpe-networking/dockerfiles. [Carlos Miguel
  Jenkins Perez]

  new: dev: Add docker file for toxin node


