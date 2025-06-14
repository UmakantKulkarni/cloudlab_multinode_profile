# -*- coding: utf-8 -*-
"""Paramaterized profile to create a multisite experiment. 
"""

import geni.portal as portal
import geni.rspec.pg as pg
import geni.rspec.igext as ig
import geni.rspec.emulab as emulab

pc = portal.Context()
request = pc.makeRequestRSpec()

def findName(lst, key):
    for pair in lst:
        if pair[0] == key:
            return pair[1]
    return None

# A list of aggregates.
Aggregates = [
    ('',  'None'),
    ('urn:publicid:IDN+emulab.net+authority+cm',        'Emulab'),
    ('urn:publicid:IDN+utah.cloudlab.us+authority+cm',   'Utah'),
    ('urn:publicid:IDN+wisc.cludlab.us.net+authority+cm','Wisconsin'),
    ('urn:publicid:IDN+clemson.cludlab.us.net+authority+cm','Clemson'),
]

# Full list of OS images
imageList = [
    ('default', 'Default Image'),
    ('urn:publicid:IDN+cloudlab.umass.edu+image+sfcs-PG0:ztx_ubuntu22',        'UBUNTU 22.04 ZTX'),
    ('urn:publicid:IDN+cloudlab.umass.edu+image+sfcs-PG0:p4_sdn',             'P4-SDN UBUNTU22'),
    ('urn:publicid:IDN+cloudlab.umass.edu+image+sfcs-PG0:BG_QOE_PRED_P4_SDN','QOE-PRED-P4-SDN'),
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU22-64-STD',        'UBUNTU22-64-STD'),
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU24-64-BETA',       'UBUNTU24-64-BETA'),
    ('urn:publicid:IDN+cloudlab.umass.edu+image+sfcs-PG0:ubuntu24lts',       'UBUNTU 24.04 LTS'),
    ('urn:publicid:IDN+utah.cloudlab.us+image+sfcs-PG0:sfc_u20_k8s_5g_uth','UBUNTU 20.04 K8s 5G Utah'),
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU18-64-STD',        'UBUNTU 18.04'),
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU22-64-ARM',        'UBUNTU22-64-ARM'),
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU20-64-STD',        'UBUNTU 20.04'),
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU16-64-STD',        'UBUNTU 16.04'),
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//CENTOS7-64-STD',         'CENTOS 7'),
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//FBSD112-64-STD',         'FreeBSD 11.2'),
]

# Define a multi‐value struct parameter: one block per “cluster” (aggregate)
ps = pc.defineStructParameter(
    'clusters', 'Clusters', [],
    multiValue=True, min=1, hide=False, multiValueTitle='Clusters',
    members=[
        portal.Parameter('cluster', 'Cluster (aggregate)',
                         portal.ParameterType.STRING,
                         Aggregates[0], Aggregates),
        portal.Parameter('count',   'Number of Nodes',
                         portal.ParameterType.INTEGER, 1),
        portal.Parameter('lan',     'Create a LAN?',
                         portal.ParameterType.BOOLEAN, False,
                         longDescription='Create a LAN among these nodes.'),
        portal.Parameter('osImage', 'OS Image for each node',
                         portal.ParameterType.IMAGE,
                         imageList[0], imageList,
                         longDescription='Select the OS image to use on these nodes.'),
        portal.Parameter('hwType', 'Hardware type for each node',
                         portal.ParameterType.NODETYPE, '',
                         longDescription='Specify a physical node type (pc3000, d710, etc).'),
    ]
)

# Bind parameters and validate
params = pc.bindParameters()
for idx, cluster in enumerate(params.clusters):
    if cluster.cluster == '':
        pc.reportError(portal.ParameterError(
            'Entry %d: must select a cluster' % (idx+1),
            ['clusters[%d].cluster' % idx]
        ))
    if cluster.count < 1:
        pc.reportError(portal.ParameterError(
            'Entry %d: count must be >= 1' % (idx+1),
            ['clusters[%d].count' % idx]
        ))
pc.verifyParameters()

# Build the RSpec
for cluster in params.clusters:
    if cluster.cluster == '':
        continue

    # Create LAN if requested
    lan = None
    if cluster.count > 1 and cluster.lan:
        lan = request.Link() if cluster.count == 2 else request.LAN()

    for i in range(cluster.count):
        # Name and instantiate node
        name = findName(Aggregates, cluster.cluster) + '-' + str(i)
        node = request.RawPC(name)
        node.component_manager_id = cluster.cluster

        # Apply per-node OS image
        if cluster.osImage and cluster.osImage != 'default':
            node.disk_image = cluster.osImage

        # Apply per-node hardware type
        if cluster.hwType:
            node.hardware_type = cluster.hwType

        # Start VNC if desired
        node.startVNC()

        # Attach to LAN
        if lan:
            iface = node.addInterface('eth1')
            lan.addInterface(iface)

# Output the RSpec
pc.printRequestRSpec(request)
