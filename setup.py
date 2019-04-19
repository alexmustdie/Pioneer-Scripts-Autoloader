#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

if __name__ == '__main__':

    requirementsFile = 'requirements.txt'

    if os.path.isfile(requirementsFile):
        os.system('pip3 install -r %s' % requirementsFile)
    else:
        print('File "%s" not found' % requirementsFile)

    input('Press any key to exit')
