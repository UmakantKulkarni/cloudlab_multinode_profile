# -*- coding: utf-8 -*-
"""Parameterized profile: define node groups and connect all together on a single LAN."""

import geni.portal as portal
import geni.rspec.pg as pg
import geni.rspec.emulab as emulab

pc      = portal.Context()
request = pc.makeRequestRSpec()

# -------------------------------------------------------------------
# Full list of OS images
# -------------------------------------------------------------------
imageList = [
    ('default', 'Default Image'),
    ('urn:publicid:IDN+cloudlab.umass.edu+image+sfcs-PG0:ztx_ubuntu22',        'UBUNTU 22.04 ZTX'),
    ('urn:publicid:IDN+cloudlab.umass.edu+image+sfcs-PG0:p4_sdn',               'P4-SDN UBUNTU22'),
    ('urn:publicid:IDN+cloudlab.umass.edu+image+sfcs-PG0:BG_QOE_PRED_P4_SDN',   'QOE-PRED-P4-SDN'),
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU22-64-STD',           'UBUNTU22-64-STD'),
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU24-64-BETA',          'UBUNTU24-64-BETA'),
    ('urn:publicid:IDN+cloudlab.umass.edu+image+sfcs-PG0:ubuntu24lts',          'UBUNTU 24.04 LTS'),
    ('urn:publicid:IDN+utah.cloudlab.us+image+sfcs-PG0:sfc_u20_k8s_5g_uth',     'UBUNTU 20.04 K8s 5G Utah'),
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU18-64-STD',           'UBUNTU 18.04'),
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU22-64-ARM',           'UBUNTU22-64-ARM'),
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU20-64-STD',           'UBUNTU 20.04'),
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU16-64-STD',           'UBUNTU 16.04'),
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//CENTOS7-64-STD',            'CENTOS 7'),
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//FBSD112-64-STD',            'FreeBSD 11.2'),
]

# -------------------------------------------------------------------
# Top-level optional parameters
# -------------------------------------------------------------------
pc.defineParameter(
    "useVMs", "Use XEN VMs", portal.ParameterType.BOOLEAN, False,
    longDescription="Create XEN VMs instead of bare-metal nodes."
)
pc.defineParameter(
    "startVNC", "Start X11 VNC on your nodes", portal.ParameterType.BOOLEAN, False,
    longDescription="Enable browser-based VNC access on each node."
)
pc.defineParameter(
    "linkSpeed", "Link Speed", portal.ParameterType.INTEGER, 0,
    [(0, "Any"), (100000, "100Mb/s"), (1000000, "1Gb/s"),
     (10000000, "10Gb/s"), (25000000, "25Gb/s"), (100000000, "100Gb/s")],
    advanced=True,
    longDescription="Specific link speed for the LAN."
)
pc.defineParameter(
    "bestEffort", "Best Effort", portal.ParameterType.BOOLEAN, False,
    advanced=True,
    longDescription="Ignore bandwidth constraints for very large LANs."
)
pc.defineParameter(
    "sameSwitch", "No Interswitch Links", portal.ParameterType.BOOLEAN, False,
    advanced=True,
    longDescription="Force all nodes on a single switch (may limit mapping)."
)
pc.defineParameter(
    "tempFileSystemSize", "Temporary Filesystem Size",
    portal.ParameterType.INTEGER, 0, advanced=True,
    longDescription="GB of ephemeral storage (deleted on teardown)."
)
pc.defineParameter(
    "tempFileSystemMax", "Temp Filesystem Max Space",
    portal.ParameterType.BOOLEAN, False, advanced=True,
    longDescription="Allocate all available disk space instead of specifying a size."
)
pc.defineParameter(
    "tempFileSystemMount", "Temporary Filesystem Mount Point",
    portal.ParameterType.STRING, "/mydata", advanced=True,
    longDescription="Mount point for the temporary filesystem."
)

# -------------------------------------------------------------------
# 1) Define a multi-value "groups" struct parameter
# -------------------------------------------------------------------
ps = pc.defineStructParameter(
    "groups", "Node Groups", [], 
    multiValue=True, min=1, hide=False, multiValueTitle="Add another node group",
    members=[
        portal.Parameter(
            "count", "Number of nodes", portal.ParameterType.INTEGER, 1,
            longDescription="How many identical nodes to create in this group."
        ),
        portal.Parameter(
            "osImage", "OS Image for these nodes",
            portal.ParameterType.IMAGE, imageList[0], imageList,
            longDescription="Select the OS image for this group."
        ),
        portal.Parameter(
            "hwType", "Hardware type for these nodes",
            portal.ParameterType.NODETYPE, "",
            longDescription="Specify a hardware type (e.g., pc3000, d710), or leave default."
        ),
    ]
)

# -------------------------------------------------------------------
# 2) Bind & validate
# -------------------------------------------------------------------
params = pc.bindParameters()

# Must have at least one group
if not params.groups:
    pc.reportError(portal.ParameterError(
        "You must define at least one node group.",
        ["groups"]
    ))

for idx, grp in enumerate(params.groups):
    if grp.count < 1:
        pc.reportError(portal.ParameterError(
            "Group %d: count must be >= 1." % (idx + 1),
            ["groups[%d].count" % idx]
        ))
    # temp FS size sanity
if params.tempFileSystemSize < 0 or params.tempFileSystemSize > 200:
    pc.reportError(portal.ParameterError(
        "Please specify a temp filesystem size between 0 and 200GB.",
        ["tempFileSystemSize"]
    ))

pc.verifyParameters()

# -------------------------------------------------------------------
# 3) Create a single LAN for all nodes
# -------------------------------------------------------------------
if sum(grp.count for grp in params.groups) > 1:
    total = sum(grp.count for grp in params.groups)
    lan = request.Link() if total == 2 else request.LAN()
    if params.bestEffort:
        lan.best_effort = True
    elif params.linkSpeed > 0:
        lan.bandwidth = params.linkSpeed
    if params.sameSwitch:
        lan.setNoInterSwitchLinks()
else:
    lan = None

# -------------------------------------------------------------------
# 4) Instantiate each node group and attach to LAN
# -------------------------------------------------------------------
node_idx = 0
for grp in params.groups:
    for _ in range(grp.count):
        name = "vm%d" % node_idx if params.useVMs else "node%d" % node_idx
        node = request.XenVM(name) if params.useVMs else request.RawPC(name)

        # OS image
        if grp.osImage and grp.osImage != "default":
            node.disk_image = grp.osImage

        # Hardware type
        if grp.hwType:
            node.hardware_type = grp.hwType

        # Attach to LAN
        if lan:
            iface = node.addInterface("eth1")
            lan.addInterface(iface)

        # Optional ephemeral blockstore
        if params.tempFileSystemSize > 0 or params.tempFileSystemMax:
            bs = node.Blockstore("%s-bs" % name, params.tempFileSystemMount)
            bs.size = "0GB" if params.tempFileSystemMax else "%dGB" % params.tempFileSystemSize
            bs.placement = "any"

        # VNC
        if params.startVNC:
            node.startVNC()

        node_idx += 1

# -------------------------------------------------------------------
# 5) Print the RSpec
# -------------------------------------------------------------------
pc.printRequestRSpec(request)
