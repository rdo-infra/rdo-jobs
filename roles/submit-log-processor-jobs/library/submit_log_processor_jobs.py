# Copyright 2013 Hewlett-Packard Development Company, L.P.
# Copyright (C) 2017 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
#
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import json
import re
import traceback

from ansible.module_utils.six.moves import urllib
from ansible.module_utils.basic import AnsibleModule

import ansible.module_utils.gear as gear


class FileMatcher(object):
    def __init__(self, name, tags):
        self._name = name
        self.name = re.compile(name)
        self.tags = tags

    def matches(self, s):
        if self.name.search(s):
            return True


class File(object):
    def __init__(self, name, tags):
        self._name = name
        self._tags = tags

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        raise Exception("Cannot update File() objects they must be hashable")

    @property
    def tags(self):
        return self._tags

    @tags.setter
    def tags(self, value):
        raise Exception("Cannot update File() objects they must be hashable")

    def toDict(self):
        return dict(name=self.name,
                    tags=self.tags)

    # We need these objects to be hashable so that we can use sets
    # below.
    def __eq__(self, other):
        return self.name == other.name

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.name)


class LogMatcher(object):
    def __init__(self, server, port, config, success, log_url, host_vars):
        self.client = gear.Client()
        self.client.addServer(server, port)
        self.hosts = host_vars
        self.zuul = list(host_vars.values())[0]['zuul']
        self.success = success
        self.log_url = log_url
        self.matchers = []
        for f in config['files']:
            self.matchers.append(FileMatcher(f['name'], f.get('tags', [])))

    def findFiles(self, path):
        results = set()
        for (dirpath, dirnames, filenames) in os.walk(path):
            for filename in filenames:
                fn = os.path.join(dirpath, filename)
                partial_name = fn[len(path) + 1:]
                for matcher in self.matchers:
                    if matcher.matches(partial_name):
                        results.add(File(partial_name, matcher.tags))
                        break
        return results

    def submitJobs(self, jobname, files):
        self.client.waitForServer(90)
        ret = []
        for f in files:
            output = self.makeOutput(f)
            output = json.dumps(output).encode('utf8')
            job = gear.TextJob(jobname, output)
            self.client.submitJob(job, background=True)
            ret.append(dict(handle=job.handle,
                            arguments=output))
        return ret

    def makeOutput(self, file_object):
        output = {}
        output['retry'] = False
        output['event'] = self.makeEvent(file_object)
        output['source_url'] = output['event']['fields']['log_url']
        return output

    def makeEvent(self, file_object):
        out_event = {}
        out_event["fields"] = self.makeFields(file_object.name)
        basename = os.path.basename(file_object.name)
        out_event["tags"] = [basename] + file_object.tags
        if basename.endswith(".gz"):
            # Backward compat for e-r which relies on tag values
            # without the .gx suffix
            out_event["tags"].append(basename[:-3])
        return out_event

    def makeFields(self, filename):
        hosts = [h for h in self.hosts.values() if 'nodepool' in h]
        zuul = self.zuul
        fields = {}
        fields["filename"] = filename
        fields["build_name"] = zuul['job']
        fields["build_status"] = self.success and 'SUCCESS' or 'FAILURE'
        # TODO: this is too simplistic for zuul v3 multinode jobs
        if hosts:
            node = hosts[0]
            fields["build_node"] = node['nodepool']['label']
            fields["build_hostids"] = [h['nodepool']['host_id'] for h in hosts
                                       if 'host_id' in h['nodepool']]
            fields["node_provider"] = node['nodepool']['provider']
        else:
            fields["build_node"] = 'zuul-executor'
            fields["node_provider"] = 'local'
        # TODO: should be build_executor, or removed completely
        fields["build_master"] = zuul['executor']['hostname']

        fields["project"] = zuul['project']['name']
        # The voting value is "1" for voting, "0" for non-voting
        fields["voting"] = int(zuul['voting'])
        # TODO(clarkb) can we do better without duplicated data here?
        fields["build_uuid"] = zuul['build']
        fields["build_short_uuid"] = fields["build_uuid"][:7]
        # TODO: this should be build_pipeline
        fields["build_queue"] = zuul['pipeline']
        # TODO: this is not interesteding anymore
        fields["build_ref"] = zuul['ref']
        fields["build_branch"] = zuul.get('branch', 'UNKNOWN')
        # TODO: remove
        fields["build_zuul_url"] = "N/A"
        if 'change' in zuul:
            fields["build_change"] = zuul['change']
            fields["build_patchset"] = zuul['patchset']
        elif 'newrev' in zuul:
            fields["build_newrev"] = zuul.get('newrev', 'UNKNOWN')
        log_url = urllib.parse.urljoin(self.log_url, filename)
        fields["log_url"] = log_url
        if 'executor' in zuul and 'hostname' in zuul['executor']:
            fields["zuul_executor"] = zuul['executor']['hostname']
        if 'attempts' in zuul:
            fields["zuul_attempts"] = zuul['attempts']
        return fields


def main():
    module = AnsibleModule(
        argument_spec=dict(
            gearman_server=dict(type='str'),
            gearman_port=dict(type='int', default=4730),
            # TODO: add ssl support
            host_vars=dict(type='dict'),
            path=dict(type='path'),
            config=dict(type='dict'),
            success=dict(type='bool'),
            log_url=dict(type='str'),
            job=dict(type='str'),
        ),
    )

    p = module.params
    results = dict(files=[], jobs=[], invocation={})
    try:
        lmc = LogMatcher(p.get('gearman_server'),
                         p.get('gearman_port'),
                         p.get('config'),
                         p.get('success'),
                         p.get('log_url'),
                         p.get('host_vars'))
        files = lmc.findFiles(p['path'])
        for f in files:
            results['files'].append(f.toDict())
        for handle in lmc.submitJobs(p['job'], files):
            results['jobs'].append(handle)
        module.exit_json(**results)
    except Exception:
        tb = traceback.format_exc()
        module.fail_json(msg='Unknown error',
                         details=tb,
                         **results)


if __name__ == '__main__':
    main()
