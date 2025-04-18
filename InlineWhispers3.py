#!/usr/bin/env python
# coding: utf=8

import os
import re
import sys
import argparse

from pathlib import Path
from shutil import copyfile

def get_new_seed():
    '''Get new seed'''
    with open('SysWhispers3/syscalls_all.h') as file:
        for line in file:
            if 'SW3_SEED' in line:
                return line
            
def replace_seed():
    '''Replace SEED in the new file'''
    new_seed = get_new_seed()

    replacement = ''
    with open('output/syscalls.h', 'r') as file:
        for line in file:
            line = line.strip()
            changes = line.replace('$$SEED$$', new_seed)
            replacement = replacement + changes + '\n'
    with open('output/syscalls.h', 'w') as file:
        file.write(replacement)
        print("[+] New seed added to syscalls.h")

def replace_extern():
    '''Replace EXTERN_C definitions in the new file'''
    replacement = ''
    actual_extern_c = ''
    is_extern_part = False
    with open('output/syscalls.h', 'r') as file:
        for line in file:
            line = line.strip()
            if 'EXTERN_C NTSTATUS' in line:
                actual_extern_c = line.replace('EXTERN_C NTSTATUS', '').replace('(', '').replace(')', '').replace(';', '').replace(' ', '')
                is_extern_part = True
            if is_extern_part and ';' in line:
                changes = line.replace(';', f' asm("{actual_extern_c}");')

            if '#include <windows.h>' in line:
                changes = line.replace('#include <windows.h>', '#include <windows.h>\n#include "syscalls-asm.h"')
            else:
                changes = line
            replacement = replacement + changes + '\n'
    with open('output/syscalls.h', 'w') as file:
        file.write(replacement)

def create_asm_file():
    '''Create asm stubs file'''
    replacement = ''
    with open('SysWhispers3/syscalls_all_-asm.x64.asm', 'r') as file:
        for line in file:
            line = line.strip()

            if '.code' in line:
                line = line.replace('.code', '#pragma once\r\n#include <windows.h>\r\n\r\n#if _WIN64')
            if 'EXTERN SW3_GetSyscallNumber: PROC' in line:
                line = line.replace('EXTERN SW3_GetSyscallNumber: PROC', '')
            if 'EXTERN SW3_GetSyscallAddress: PROC' in line:
                line = line.replace('EXTERN SW3_GetSyscallAddress: PROC', '')
            if 'PROC' in line:
                func_nt = line.split(' ', 1)[0]
                func_zw = func_nt.replace('Nt', 'Zw')
                line = line.replace(f'{func_nt} PROC', f'#define {func_zw} {func_nt}\r\n__asm__("{func_nt}: \\n\\')
            if ';' in line:
                line = line.split(';', 1)[0]
            if 'sub rsp, 28h' in line:
                line = line.replace('sub rsp, 28h', 'sub rsp, 0x28').rstrip() + ' \\n\\'
            if 'add rsp, 28h' in line:
                line = line.replace('add rsp, 28h', 'add rsp, 0x28').rstrip() + ' \\n\\'
            if 'mov ecx,' in line:
                line = line.replace('mov ecx, ', 'mov ecx, 0x').rstrip()[:-1]
            if line.startswith('call'):
                line = line.rstrip() + ' \\n\\'
            if line.startswith('mov'):
                line = line.rstrip() + ' \\n\\'
            if line.startswith('syscall'):
                line = line.rstrip() + ' \\n\\'
            if line.startswith('ret'):
                line = line.rstrip() + ' \\n\\'
            if line.startswith('jmp'):
                line = line.rstrip() + ' \\n\\'
            if 'ENDP' in line:
                line = '");'

            if line.startswith('end'):
                line = '#endif'

            changes = line
            replacement = replacement + changes + '\n'

    with open('output/syscalls-asm.h', 'w') as file:
        file.write(replacement)

def remove_specific_includes(content):
    '''Remove #include "syscalls.h", #include "syscalls-asm.h", and #include "syscalls.c" statements from the content'''
    return re.sub(r'#(include ("syscalls(.h"|-asm.h"|.c")|<windows.h>)|pragma once)', '', content)

def merge_to_aio():
    '''Merge all files to one usable .h file'''
    with open('output/syscalls-aio.h', 'w') as aio:
        with open('output/syscalls.h', 'r') as sys_h, \
             open('output/syscalls.c', 'r') as sys_c, \
             open('output/syscalls-asm.h', 'r') as sys_asm:
            
            aio.write("#pragma once\n#include <windows.h>\n")
            aio.write(remove_specific_includes(sys_h.read()))
            aio.write('\n') 
            aio.write(remove_specific_includes(sys_c.read()))
            aio.write('\n')
            aio.write(remove_specific_includes(sys_asm.read()))

if __name__ == '__main__':
	'''Main'''
	print(".___       .__  .__              __      __.__    .__                                   ________  ")
	print("|   | ____ |  | |__| ____   ____/  \\    /  \\  |__ |__| ____________   ___________  _____\\_____  \\ ")
	print("|   |/    \\|  | |  |/    \\_/ __ \\   \\/\\/   /  |  \\|  |/  ___/\\____ \\_/ __ \\_  __ \\/  ___/ _(__  < ")
	print("|   |   |  \\  |_|  |   |  \\  ___/\\        /|   Y  \\  |\\___ \\ |  |_> >  ___/|  | \\/\\___ \\ /       \\ ")
	print("|___|___|  /____/__|___|  /\\___  >\\__/\\  / |___|  /__/____  >|   __/ \\___  >__|  /____  >______  /")
	print("         \\/             \\/     \\/      \\/       \\/        \\/ |__|        \\/           \\/       \\/")
	print("\r\ntdeerenberg - https://github.com/tdeerenberg\r\n")

	if not os.path.isdir('SysWhispers3') or not os.path.isfile('SysWhispers3/syscalls_all.h'):
		print('[ERROR] SysWhispers3 not present, to fix:\r\n')
		print('git clone https://github.com/klezVirus/SysWhispers3')
		print('cd SysWhispers3/ && python3 syswhispers.py -p all -a x64 -m jumper -o syscalls_all && cd ..\r\n')
		sys.exit(0)

	# Create output directory with the new templates
	Path('output').mkdir(parents=True, exist_ok=True)
	copyfile('syscalls.c.template', 'output/syscalls.c')
	copyfile('syscalls.h.template', 'output/syscalls.h')

	parser = argparse.ArgumentParser()
	parser.add_argument('--aio', action='store_true', help="Trigger the aio flag")
	args = parser.parse_args()

	# Replace EXTERN_C in syscalls.h
	print("[+] Replacing EXTERN_C in syscalls.h")
	replace_extern()
	print("[+] Replaced EXTERN_C in syscalls.h")

	# Create asm stub with the correct syscalls format
	print("[+] Creating syscalls-asm.c with indirect syscall instructions")
	create_asm_file()
	print("[+] Done creating syscalls-asm.c\n")

	if args.aio:
		print('[+] All in One flag detected, merging syscalls.c, syscalls.h, and syscalls-asm.h into one file')
		merge_to_aio()
		print("[+] Merged into one usable file: syscalls-aio.h\n")
		print("Import syscalls-aio.h in your project and include syscalls-aio.h to use indirect syscalls, or:")

	print("Import syscalls.c syscalls.h, syscalls-asm.h in your project and include syscalls.c to start to use syscalls")


