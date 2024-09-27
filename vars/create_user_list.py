#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-

# FIXME: this should be dynamically generated inside ansible
# But it's quite complex, and will be faster that way

import os
import sys
import yaml
import json
import argparse

class GridUser:
    def __init__(self, name, uid, gid, groups=None):
        self.name = name
        self.uid = uid
        self.gid = gid
        self.groups = groups

    def __str__(self):
        # Return the user as a line
        return self.name + ' ' + str(self.uid) + ' ' + str(self.gid)
    
    def to_yaml(self):
        if (self.groups == None):
            return {'name': self.name, 'uid': self.uid, 'gid': self.gid}
        return {'name': self.name, 'uid': self.uid, 'gid': self.gid, 'groups': self.groups}

def to3digits(n):
    s = str(n)
    if len(s) == 1:
        return '00' + s
    elif len(s) == 2:
        return '0' + s
    else:
        return s


class OneRole:
    def __init__(self, ydata):
        self.name = ydata['name']
        self.fqan = ydata['fqan']
        self.gid = int(ydata['gid'])
    def __str__(self):
        # Return the role as a line
        return self.name + ' ' + self.fqan + ' ' + str(self.gid)

    def generate_user_list(self,vo):
        # Generate a list of users
        user_list = []
        if (vo.gid == self.gid): # Main group
            for i in range(200):
                uid = vo.gid + i
                name = vo.name + to3digits(i)
                roles = [self.name]
                user_list.append(GridUser(name, uid, self.gid))
        else:
            base_uid=vo.gid+500*(self.gid-vo.gid)
            for i in range(21):
                uid = base_uid + i
                if (i==0):
                    name = vo.name+ '_' + self.name
                else:
                    name = vo.name + '_' + self.name + to3digits(i)
                user_list.append(GridUser(name, uid, self.gid, vo.gid))
        return user_list
        

class OneVo(OneRole):
    def __init__(self, ydata):
        self.name = ydata['name']
        self.fqan = ydata['fqan']
        self.gid = int(ydata['gid'])
        # first check if there are roles
        self.roles = []
        if 'roles' in ydata:
            roles = ydata['roles']
            for one_role in roles:
                self.roles.append(OneRole(one_role))
    
    def generate_user_list(self):
        # Generate a list of users
        user_list = []
        user_list = user_list + super().generate_user_list(self)
        for one_role in self.roles:
            user_list = user_list + one_role.generate_user_list(self)
        return user_list

    def __str__(self):
        # Return the VO as a line for each role
        s=self.name + ' ' + self.fqan + ' ' + str(self.gid)
        for one_role in self.roles:
            s = s + '\n    ' + str(one_role)
        return s

def main():
    # Parsing supported_vos.yaml
    data = yaml.safe_load(open('supported_vos.yaml', 'r'))
    #print (data)
    #return
    vo_list = []
    for one_vo in data['vo_details']:
        vo_list.append(OneVo(one_vo))
    
    # Generate the user list
    user_list = []
    for vo in vo_list:
        user_list = user_list + vo.generate_user_list()
    
    # convert user list to yaml
    user_list_yaml = [user.to_yaml() for user in user_list]

    # Final dictionary
    grid_users = {'grid_users': user_list_yaml}
    # Write the user list in yaml
    with open('user_list.yaml', 'w') as f:
        yaml.safe_dump(grid_users, f, default_flow_style=False, sort_keys=False)


if __name__ == "__main__":
    main()