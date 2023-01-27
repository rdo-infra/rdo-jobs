# Python script to automatically generate roles content for install_yamls
# To Run: python makefile_to_install_yamls.py <path to install_yamls makefile>
import os
import sys
import yaml 

script_path = os.path.realpath(os.path.dirname(__file__))
additional_commands_file = os.path.join(script_path, 'additional_commands_between_makefile_target.yaml')
roles_dir = os.path.join(os.path.normpath(script_path + os.sep + os.pardir), 'roles', 'use_install_yamls')
template_file = os.path.join(roles_dir, 'templates', 'install_yamls.sh.j2')
roles_var_file = os.path.join(roles_dir, 'defaults', 'main.yaml')
make_file = sys.argv[1]

# Content to dump in defaults/main.yaml
roles_vars = []

# Jinja conditionals to export makefile vars
export_jinja_vars = []

# Jinja conditionals to run commands
command_jinja_vars = []

# Jinja conditionals to run cleanup commands
command_cleanup_jinja_vars = []

# Read the content of MakeFile
with open(make_file) as f:
    content = f.read().split('\n')

# Read the content of additional_commands_between_makefile_target.yaml
with open(additional_commands_file) as yd:
    yaml_data = yaml.safe_load(yd)

# Function to look for specific yaml key and return the
# command value
def additional_command_between_make_target(key_name, data=yaml_data):
    if key_name in data:
        return data[key_name]
    else:
        return '\n'

# Seperate vars in order to export it
for data in content:
    # In Makefile, vars should contain ?=
    if '?=' in data:
        k, v = data.split('?=')
        key = k.strip()
        value = v.strip()
        roles_vars.append(f'''
## The default value of {key.lower()} is {value}
# {key.lower()}: {value}''')
        # contstruct jinja for exporting makefile vars
        export_jinja_vars.append(f'''
{{% if {key.lower()} is defined %}}
# To set the value of {key}
export {key}={{{{ {key.lower()} }}}}
{{% endif %}}''')

# Seperate commands
for data in content:
    if data.startswith('.PHONY: '):
        command = data.split('.PHONY: ')[1]
        roles_vars.append(f'''
# For running **make {command}**
# Set the value of run_{command} to true
# run_{command}: false''')

        if command.endswith('cleanup'):
            command_cleanup_jinja_vars.append(f'''
{{% if run_{command} is defined and run_{command} | bool %}}
# set run_{command} var to true to run **make {command}**
make {command}
{additional_command_between_make_target(command)}
{{% endif %}}''')
        else:
            command_jinja_vars.append(f'''
{{% if run_{command} is defined and run_{command} | bool %}}
# set run_{command} var to true to run **make {command}**
make {command}
{additional_command_between_make_target(command)}
{{% endif %}}''')

# Reverse the order of cleanup command
command_cleanup_jinja_vars.reverse()

# Additional Vars which are not defined in makefile
additional_vars = [
"""
# To run *make crc_storage* command
# set run_crc_storage to true

# To run *make crc_storage_cleanup* command
# set run_crc_storage_cleanup to true
"""]

additional_commands = ["""
{% if run_crc_storage is defined and run_crc_storage| bool %}
make crc_storage
{% endif%}
"""]

additional_cleanup_commands = ["""
{% if run_crc_storage_cleanup is defined and run_crc_storage_cleanup| bool %}
make crc_storage_cleanup
{% endif%}
"""]

# Merge list
command_list = export_jinja_vars + additional_commands + command_jinja_vars + command_cleanup_jinja_vars + additional_cleanup_commands

## Write content in the file
# defaults/main.yaml
with open(roles_var_file, 'w') as f:
    f.write('\n'.join(roles_vars + additional_vars))

# templates/run_install_yamls.sh.j2
with open(template_file, 'w') as f:
    f.write('\n'.join(command_list))
