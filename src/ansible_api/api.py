#!/usr/bin/env python
# coding: utf-8

# A restful HTTP API for ansible by tornado
# Base on ansible 2.x
# Github <https://github.com/lfbear/ansible-api>
# Author: lfbear

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from collections import namedtuple
from collections import MutableMapping
from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager
from ansible.inventory import Inventory
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.plugins.callback.log_plays import CallbackModule
from ansible_api.detail import DetailProcess


class Api(object):

    @staticmethod
    def runCmd(target, module, arg, sudo, forks):
        # initialize needed objects
        variable_manager = VariableManager()
        loader = DataLoader()
        Options = namedtuple('Options', ['listtags', 'listtasks', 'listhosts',
                                         'syntax', 'connection', 'module_path', 'forks', 'remote_user',
                                         'private_key_file', 'ssh_common_args', 'ssh_extra_args',
                                         'sftp_extra_args', 'scp_extra_args', 'become', 'become_method',
                                         'become_user', 'verbosity', 'check'])
        pb_options = Options(listtags=False, listtasks=False,
                             listhosts=False, syntax=False, connection='ssh',
                             module_path=None, forks=forks, remote_user='ansible',
                             private_key_file=None, ssh_common_args=None,
                             ssh_extra_args=None, sftp_extra_args=None, scp_extra_args=None,
                             become=sudo, become_method='sudo', become_user='root',
                             verbosity=None, check=False)

        passwords = {}

        # create inventory and pass to var manager
        inventory = Inventory(
            loader=loader, variable_manager=variable_manager)
        variable_manager.set_inventory(inventory)

        # create play with tasks
        play_source = dict(
            name="Ansible Shell Task",
            hosts=target,
            gather_facts='no',
            tasks=[
                dict(action=dict(module=module, args=arg))
            ]
        )
        play = Play().load(play_source, variable_manager=variable_manager, loader=loader)

        cb = CallbackModule()
        tqm = None
        try:
            tqm = TaskQueueManager(
                inventory=inventory,
                variable_manager=variable_manager,
                loader=loader,
                options=pb_options,
                passwords=passwords,
                stdout_callback=cb,
            )
            rc = tqm.run(play)
            d = DetailProcess(tqm._prst)
        finally:
            if tqm is not None:
                tqm.cleanup()
        return {'rc': rc, 'detail': d.run()}

    @staticmethod
    def runPlaybook(yml_file, myvars, forks):
        # initialize needed objects
        variable_manager = VariableManager()
        loader = DataLoader()
        Options = namedtuple('Options', ['listtags', 'listtasks', 'listhosts',
                                         'syntax', 'connection', 'module_path', 'forks', 'remote_user',
                                         'private_key_file', 'ssh_common_args', 'ssh_extra_args',
                                         'sftp_extra_args', 'scp_extra_args', 'become', 'become_method',
                                         'become_user', 'verbosity', 'check'])
        pb_options = Options(listtags=False, listtasks=False,
                             listhosts=False, syntax=False, connection='ssh',
                             module_path=None, forks=forks, remote_user='ansible',
                             private_key_file=None, ssh_common_args=None,
                             ssh_extra_args=None, sftp_extra_args=None, scp_extra_args=None,
                             become=True, become_method='sudo', become_user='root',
                             verbosity=None, check=False)

        passwords = {}

        # create inventory and pass to var manager
        inventory = Inventory(
            loader=loader, variable_manager=variable_manager)
        variable_manager.set_inventory(inventory)
        variable_manager.extra_vars = myvars
        pbex = PlaybookExecutor(playbooks=[yml_file],
                                inventory=inventory, variable_manager=variable_manager, loader=loader,
                                options=pb_options, passwords=passwords)
        rc = pbex.run()
        # print((pbex._tqm._prst))
        pbex._tqm._stdout_callback = CallbackModule()
        # parse result detail
        d = DetailProcess(pbex._tqm._prst)
        return {'rc': rc, 'detail': d.run()}
