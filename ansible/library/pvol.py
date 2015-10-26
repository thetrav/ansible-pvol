#!/usr/bin/python

DOCUMENTATION = '''
---
module: pvol
author: "Travis Dixon (@thetrav)"
version_added: "0.1"
short_description: Manage LVM physical volumes
requirements: [ lvm2 ]
description:
    - Manage LVM physical volumes
options:
    device:
        required: true
        description:
            - Device to select (eg: /dev/sdb1)
    state:
        default: present
        choices: [ present, absent ]
        description:
            - Device to select (eg: /dev/sdb1)
'''

EXAMPLES = '''
# add a physical volume
- partition: device=/dev/sdb1
# remove a physical volume
- partition: device=/dev/sdb1 state=absent
'''

def read_fixed_width_table(table):
    titles = [title.strip() for title in table[0].split()]
    
    column_starts = [table[0].index(title) for title in titles]
    column_ends = [num - 1 for num in column_starts[1:]] + [len(table[0])]
    columns = zip(column_starts, column_ends)
    def record(line):
        values = [line[column[0]:column[1]].strip() for column in columns]
        return dict(zip(titles, values))
    return [ record(line) for line in table[1:] ]


class Lvm(object):
    def __init__(self, run_command):
        self.command_runner = run_command

    def run_command(self, cmd):
        rc, stdout, stderr = self.command_runner(cmd)
        if rc != 0:
            raise ValueError("{} {} {} {}".format(rc, stdout, stderr, cmd))
        return (stdout, stderr)

    def refresh(self):
        stdout, stderr = self.run_command("pvs")
        rows = read_fixed_width_table(stdout.split("\n"))
        self.volumes = [row['PV'] for row in rows]

    def set_volume(self, device):
        self.refresh()
        if device in self.volumes:
            return False
        stdout, stderr = self.run_command("pvcreate {}".format(device))
        self.refresh()
        return True


    def remove_volume(self, device):
        self.refresh()
        if device not in self.volumes:
            return False
        stdout, stderr = self.run_command("pvremove {}".format(device))
        self.refresh()
        return True

def main():
    module = AnsibleModule(
        argument_spec = dict(
            device=dict(required=True, type='str'),
            state=dict(default='present', choices=['present', 'absent'], type='str')
        ),
        supports_check_mode=True)
    def param(key):
        return module.params[key]

    result = {}

    lvm = Lvm(module.run_command)
    state = param('state')

    if state == 'present':
        result['changed'] = lvm.set_volume(param('device'))
    if state == 'absent':
        result['changed'] = lvm.remove_volume(param('device'))
    
    result['pvols'] = lvm.volumes
    module.exit_json(**result)


# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
