# -*- coding: utf-8 -*-
"""Parameterized profile to create a multisite experiment via multiple LANs.

Each “LAN” block lets you choose:
 - which CloudLab site (aggregate) to use,
 - how many nodes to request on that LAN,
 - which OS image each node should run,
 - which hardware type each node should use.

Click “Add another LAN block” to create LAN1, LAN2, etc., and at the end
all of those LANs will be interconnected.
"""

import geni.portal as portal
import geni.rspec.pg as pg
import geni.rspec.igext as ig
import geni.rspec.emulab as emulab

pc      = portal.Context()
request = pc.makeRequestRSpec()

# -------------------------------------------------------------------
# Full list of OS images
# -------------------------------------------------------------------
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

# -------------------------------------------------------------------
# 1) Define a multi-value "lans" struct parameter
# -------------------------------------------------------------------
ps = pc.defineStructParameter(
    'lans', 'LANs', [],
    multiValue       = True,
    min              = 1,
    hide             = False,
    multiValueTitle  = 'Add another LAN block',
    members = [
        portal.Parameter(
            'site', 'CloudLab site (aggregate)',
            portal.ParameterType.AGGREGATE, '',
            longDescription='Select which CloudLab site to run this LAN on.'
        ),
        portal.Parameter(
            'count', 'Number of Nodes', portal.ParameterType.INTEGER, 1,
            longDescription='How many nodes to request on this LAN.'
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

for idx, lanblock in enumerate(params.lans):
    if lanblock.count < 1:
        pc.reportError(portal.ParameterError(
            'LAN %d: node count must be at least 1.' % (idx + 1),
            ['lans[%d].count' % idx]
        ))
    # we allow an empty site (use default) if desired

pc.verifyParameters()

# -------------------------------------------------------------------
# 3) Build the RSpec
# -------------------------------------------------------------------
all_nodes = []

for lanblock in params.lans:
    # derive short name from site URN, e.g. urn:...+emulab.net+... → "emulab"
    if lanblock.site:
        parts = lanblock.site.split('+')
        short = parts[1].split('.')[0] if len(parts) > 1 else 'site'
    else:
        short = 'site'

    # Create this LAN
    lan = None
    if lanblock.count > 1:
        lan = request.Link() if lanblock.count == 2 else request.LAN()

    # instantiate nodes in this LAN
    for i in range(lanblock.count):
        node_name = '%s-%d' % (short, i)
        node = request.RawPC(node_name)
        if lanblock.site:
            node.component_manager_id = lanblock.site

        if lanblock.osImage and lanblock.osImage != 'default':
            node.disk_image = lanblock.osImage

        if lanblock.hwType:
            node.hardware_type = lanblock.hwType

        node.startVNC()

        if lan:
            iface = node.addInterface('eth1')
            lan.addInterface(iface)

        all_nodes.append(node)

# -------------------------------------------------------------------
# 4) Interconnect all LANs together
# -------------------------------------------------------------------
if len(all_nodes) > 1:
    backbone = request.LAN()
    for node in all_nodes:
        iface = node.addInterface('eth2')
        backbone.addInterface(iface)

# -------------------------------------------------------------------
# 5) Output RSpec
# -------------------------------------------------------------------
pc.printRequestRSpec(request)
