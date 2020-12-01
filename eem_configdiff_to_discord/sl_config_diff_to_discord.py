::cisco::eem::event_register_syslog pattern "CONFIG_I" maxrun 60
#
# Copyright (c) 2017  Joe Clarke <jclarke@cisco.com>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS ``AS IS'' AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGE.
#
# This script requires the following EEM environment variables to be defined:
#
# discord_token : Bearer token for your Discord user/bot
# user_room  : Discord room name to which messages will be sent
# device_name : Device name from which the messages will be sent
#
# E.g.:
#
# event manager environment discord_token Bearer 1234abd...
# event manager environment user_room Network Operators
# event manager environment device_name C3850
#

import eem
import sys
import os
import requests
import re

CFG_BAK_PY =  '/bootflash/guest-share/running-config.bak'
CFG_BAK_IOS = 'bootflash:guest-share/running-config.bak'
DISCORD_API = 'https://discordapp.com/api/v6/webhooks/'

# Get the CLI event variables for this specific event.
arr_einfo = eem.event_reqinfo()
# Get the environment variables
bin_arr_envinfo = eem.env_reqinfo()

arr_envinfo = {key.decode('utf-8'): value.decode('utf-8') for (key, value) in bin_arr_envinfo.items()}

if 'discord_token' not in arr_envinfo:
    eem.action_syslog(
        'Environment variable "discord_token" must be set', priority='3')
    sys.exit(1)
if 'user_room' not in arr_envinfo:
    eem.action_syslog(
        'Environment variable "user_room" must be set', priority='3')
    sys.exit(1)
if 'device_name' not in arr_envinfo:
    eem.action_syslog(
        'Environment variable "device_name" must be set', priority='3')
    sys.exit(1)

# Get a CLI handle
cli = eem.cli_open()
eem.cli_exec(cli, 'enable')

if not os.path.isfile(CFG_BAK_PY):
    try:
        eem.cli_write(cli, 'copy runn {}'.format(CFG_BAK_IOS))
        prom = eem.cli_read_pattern(cli, '(filename|#)')
        if re.search(r'filename', prom):
            eem.cli_exec(cli, '\r')
    except Exception as e:
        eem.action_syslog('Failed to backup configuration to {}: {}'.format(
            CFG_BAK_IOS, e), priority='3')
        sys.exit(1)
    # First time through, only save the current config
    eem.cli_close(cli)
    sys.exit(0)

res = None
try:
    res = eem.cli_exec(
        cli, 'show archive config diff {} system:running-config'.format(CFG_BAK_IOS))
    os.remove(CFG_BAK_PY)
    eem.cli_write(cli, 'copy runn {}'.format(CFG_BAK_IOS))
    prom = eem.cli_read_pattern(cli, 'filename')
    if re.search(r'filename', prom):
        eem.cli_exec(cli, '\r')
except Exception as e:
    eem.action_syslog(
        'Failed to get config differences: {}'.format(e), priority='3')
    sys.exit(1)

eem.cli_close(cli)

diff_lines = re.split(r'\r?\n', res)
if re.search('No changes were found', res):
    # No differences found
    sys.exit(0)

device_name = arr_envinfo['device_name']
msg = '### Alert: Config changed on ' + device_name + '\n'
msg += 'Configuration differences between the running config and last backup:\n'
msg += '```{}```'.format('\n'.join(diff_lines[:-1]))

headers = {
            'content-type': 'application/json'
        }

# Post the message to Discord
url = DISCORD_API + arr_envinfo['discord_token']
payload = {'username': arr_envinfo['user_room'], 'content': msg}

try:
    r = requests.request(
        'POST', url, json=payload, headers=headers)
    r.raise_for_status()
except Exception as e:
    eem.action_syslog(
        'Error posting message to Discord: {}'.format(e), priority='3')
    sys.exit(1)
