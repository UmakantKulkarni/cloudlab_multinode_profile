# -*- coding: utf-8 -*-
"""Paramaterized profile to create a multisite experiment.

Each “cluster” block lets you choose:
 - which CloudLab aggregate (site) to use,
 - how many nodes to request,
 - whether to put them on a LAN,
 - which OS image each node should run,
 - which hardware type each node should use.

Click the “+ Clusters” button to add as many blocks as you need.
"""

import geni.portal as portal
import geni.rspec.pg as pg
import geni.rspec.igext as ig
import geni.rspec.emulab as emulab

pc = portal.Context()
request = pc.makeRequestRSpec()

# -------------------------------------------------------------------
# Full list of OS images
# -------------------------------------------------------------------
imageList = [
    ('default',    'Default Image'),
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

# -------------------------------------------------------------------
# 1) Define a multi-value "clusters" struct parameter
# -------------------------------------------------------------------
ps = pc.defineStructParameter(
    'clusters', 'Clusters', [],
    multiValue       = True,
    min              = 1,
    hide             = False,
    multiValueTitle  = 'Add another cluster block',
    members = [
        portal.Parameter(
            'cluster', 'Cluster (site)', portal.ParameterType.AGGREGATE, '',
            longDescription='Select which CloudLab aggregate (site) to use.'
        ),
        portal.Parameter(
            'count', 'Number of Nodes', portal.ParameterType.INTEGER, 1,
            longDescription='How many nodes to request at this site.'
        ),
        portal.Parameter(
            'lan', 'Create a LAN?', portal.ParameterType.BOOLEAN, False,
            longDescription='If checked, interconnect these nodes on a LAN.'
        ),
        portal.Parameter(
            'osImage', 'OS Image for each node',
            portal.ParameterType.IMAGE, imageList[0], imageList,
            longDescription='Select the OS image to install on these nodes.'
        ),
        portal.Parameter(
            'hwType', 'Hardware type for each node',
            portal.ParameterType.NODETYPE, '',
            longDescription='Specify a hardware type (e.g., pc3000, d710), or leave default.'
        ),
    ]
)

# -------------------------------------------------------------------
# 2) Bind & validate
# -------------------------------------------------------------------
params = pc.bindParameters()

# Validate each cluster block
for idx, cluster in enumerate(params.clusters):
    if cluster.count < 1:
        pc.reportError(portal.ParameterError(
            'Entry %d: count must be >= 1.' % (idx + 1),
            ['clusters[%d].count' % idx]
        ))
# we allow an empty cluster value to use the default (local) site

pc.verifyParameters()

# -------------------------------------------------------------------
# 3) Build the RSpec
# -------------------------------------------------------------------
for cluster in params.clusters:
    # Derive a short site name from the URN, e.g. "emulab.net" → "emulab"
    if cluster.cluster:
        parts = cluster.cluster.split('+')
        if len(parts) > 1:
            short = parts[1].split('.')[0]
        else:
            short = 'site'
    else:
        short = 'site'

    # Create a LAN object if requested
    lan = None
    if cluster.count > 1 and cluster.lan:
        if cluster.count == 2:
            lan = request.Link()
        else:
            lan = request.LAN()

    for i in range(cluster.count):
        # Name nodes as "<short>-<index>"
        name = '%s-%d' % (short, i)
        node = request.RawPC(name)
        if cluster.cluster:
            node.component_manager_id = cluster.cluster

        # Apply per-node OS image
        if cluster.osImage and cluster.osImage != 'default':
            node.disk_image = cluster.osImage

        # Apply per-node hardware type
        if cluster.hwType:
            node.hardware_type = cluster.hwType

        # Start VNC if desired
        node.startVNC()

        # Attach to LAN if created
        if lan:
            iface = node.addInterface('eth1')
            lan.addInterface(iface)

# Print the RSpec to the enclosing page
pc.printRequestRSpec(request)
