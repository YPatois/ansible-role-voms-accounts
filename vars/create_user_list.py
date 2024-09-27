#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# FIXME: this should be dynamically generated inside ansible
# But it's quite complex, and will be faster that way

import os
import sys
import yaml
import json
import argparse

class GridUser:
    def __init__(self):
        self.name = ''
        self.uid = ''
        self.gid = ''
        self.roles = []

    def __init__(self, name, uid, gid, roles):
        self.name = name
        self.uid = uid
        self.gid = gid
        self.roles = roles

def generate_pool_users(name, base_uid, gid, roles):
    return


class OneRole:
    def __init__(self, ydata):
        self.name = ydata['name']
        self.fqan = ydata['fqan']
        self.gid = ydata['gid']

    def __str__(self):
        # Return the role as a line
        return self.name + ' ' + self.fqan + ' ' + str(self.gid)

class OneVo:
    def __init__(self, ydata):
        self.name = ydata['name']
        self.fqan = ydata['fqan']
        self.gid = ydata['gid']
        # first check if there are roles
        self.roles = []
        if 'roles' in ydata:
            roles = ydata['roles']
            for one_role in roles:
                self.roles.append(OneRole(one_role))
    
    def __str__(self):
        # Return the VO as a line for each role
        s=self.name + ' ' + self.fqan + ' ' + str(self.gid)
        for one_role in self.roles:
            s = s + '\n    ' + str(one_role)
        return s

def main():
    # Parsing supported_vos.yaml
    data = yaml.safe_load(open('supported_vos.yaml', 'r'))
    vo_list = []
    for one_vo in data['vo_details']:
        vo_list.append(OneVo(one_vo))
    
    # Write the list
    with open('user_list.txt', 'w') as f:
        for one_vo in vo_list:
            f.write(str(one_vo) + '\n')


if __name__ == "__main__":
    main()