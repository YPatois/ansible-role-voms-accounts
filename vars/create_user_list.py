#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-

# FIXME: this should be dynamically generated inside ansible
# But it's quite complex, and will be faster that way

import os
import sys
import re
import yaml
import json
import argparse


# Linux user and group names (may be) limited to 32 characters
# Some chars are not allowed
MAX_NAME_LENGTH = 32
def sanitize_name(name):
    # Sanitize the name, removing . - etc
    name=name.replace('-','_')
    name=name.replace('.','_')

    if len(name) > MAX_NAME_LENGTH:
        length = len(name)
        splitted = name.split('_')
        if len(splitted) > 1:
            # just remove a few letters from the inside of each groups but last
            # to make the name shorter
            for i in range(len(splitted) - 1):
                if len(splitted[i]) > 4:
                    # Remove all but first and last two letters
                    splitted[i] = splitted[i][:2] + splitted[i][-2:]
            # concatenate
            name = ''.join(splitted)
    # removing underscores too
    name = name.replace('_','')

    if len(name) > MAX_NAME_LENGTH:
        raise ValueError('Name too long: ' + name)
    return name


class GridGroup:
    def __init__(self, name, gid,vo=None):
        if (not vo):
            self.name = name
        else:
            self.name = vo.name + '_' + name
        print("Creating group: " + self.name + ' ' + str(gid))
    
        self.gid = gid
        self.users = []
    
    def sanitize_name(self):
        # Sanitize the name
        self.name = sanitize_name(self.name)
    
    def __str__(self):
        # Return the group as a line
        return self.name + ' ' + str(self.gid)

    def to_yaml(self):
        #self.sanitize_name()
        return {
            'name': "Ensuring " + self.name + " group exists",
            'ansible.builtin.group': 
                {'name': self.name, 'gid': self.gid, 'state': 'present'}
        }


class GridGroups:
    def __init__(self):
        self.groups = {}

    def add_group(self, group):
        if group.gid in self.groups:
            raise ValueError('Duplicate gid: ' + str(group.gid))
        self.groups[group.gid] = group

    def sanitize_name(self):
        for group in self.groups.values():
            group.sanitize_name()

    def gid_to_name(self, gid):
        return self.groups[gid].name
    
    def to_yaml(self):
        #self.sanitize_name()
        groups = []
        for group in self.groups.values():
            groups.append(group.to_yaml())
        return groups

allgroups=GridGroups()

class GridUser:
    def __init__(self, name, uid, gid, groups=None):
        self.name = name
        self.uid = uid
        self.gid = gid
        self.groups = groups

    def sanitize_name(self):
        # Sanitize the name
        self.name = sanitize_name(self.name)

    def __str__(self):
        # Return the user as a line
        return self.name + ' ' + str(self.uid) + ' ' + str(self.gid)
    
    def to_yaml(self):
        self.sanitize_name()
        maingroup=allgroups.gid_to_name(self.gid)
        if (self.groups == None):
            return {'name': self.name, 'uid': self.uid, 'group': maingroup}
        secondgroup=allgroups.gid_to_name(self.groups)
        return {'name': self.name, 'uid': self.uid, 'groups': maingroup+','+ secondgroup}

def to3digits(n):
    s = str(n)
    if len(s) == 1:
        return '00' + s
    elif len(s) == 2:
        return '0' + s
    else:
        return s


class OneRole:
    def __init__(self, ydata,vo):
        self.name = ydata['name']
        self.fqan = ydata['fqan']
        self.gid = int(ydata['gid'])
        self.vo = vo
        allgroups.add_group(GridGroup(self.name, self.gid,self.vo))

    def __str__(self):
        # Return the role as a line
        return self.name + ' ' + self.fqan + ' ' + str(self.gid)

    def generate_user_list(self):
        # Generate a list of users
        user_list = []
        # If self.vo is not defined, it's the main group
        # If self.vo is defined, it's a subgroup
        if (not hasattr(self, 'vo')):
            # Add users from the main group
            for i in range(200):
                uid = self.gid + i
                name = self.name + to3digits(i)
                roles = [self.name]
                user_list.append(GridUser(name, uid, self.gid))
        else:
            base_uid=self.vo.gid+500*(self.gid-self.vo.gid)
            for i in range(21):
                uid = base_uid + i
                if (i==0):
                    name = self.vo.name+ '_' + self.name
                else:
                    # The underscore won't be kept, but it splits the name from
                    # the number we want to keep
                    # it will be concatenate by the sanitize function
                    name = self.vo.name + '_' + self.name + '_' + to3digits(i)
                user_list.append(GridUser(name, uid, self.gid, self.vo.gid))
        return user_list
        

class OneVo(OneRole):
    def __init__(self, ydata):
        self.name = ydata['name']
        self.fqan = ydata['fqan']
        self.gid = int(ydata['gid'])
        allgroups.add_group(GridGroup(self.name, self.gid))

        self.roles = []
        if 'roles' in ydata:
            roles = ydata['roles']
            for one_role in roles:
                self.roles.append(OneRole(one_role,self))
    
    def generate_user_list(self):
        # Generate a list of users
        user_list = []
        user_list = user_list + super().generate_user_list()
        for one_role in self.roles:
            user_list = user_list + one_role.generate_user_list()
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
    
    # Sanitize the group names
    allgroups.sanitize_name()

    # Generate the user list
    user_list = []
    for vo in vo_list:
        user_list = user_list + vo.generate_user_list()
    
    # convert user list to yaml
    user_list_yaml = [user.to_yaml() for user in user_list]

    # Final dictionary for user
    grid_users = {'grid_users': user_list_yaml}
    # Write the user list in yaml
    with open('../tasks/create_users.yaml', 'w') as f:
        yaml.safe_dump(grid_users, f, default_flow_style=False, sort_keys=False)
    
    # Generate the group list
    group_list_yaml = allgroups.to_yaml()
    # Write the group list in yaml
    with open('../tasks/create_groups.yaml', 'w') as f:
        yaml.safe_dump(group_list_yaml, f, default_flow_style=False, sort_keys=False)


if __name__ == "__main__":
    main()