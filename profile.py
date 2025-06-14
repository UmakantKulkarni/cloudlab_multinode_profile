# -*- coding: utf-8 -*-
"""Variable number of nodes in a LAN. You have the option of picking from one
of several standard images we provide, or just use the default (typically a recent
version of Ubuntu). You may also optionally pick different hardware types
and OS images on a per-node basis.

Instructions:
Wait for the experiment to start, and then log into one or more of the nodes
by clicking on them in the topology, and choosing the `shell` menu option.
Use `sudo` to run root commands.
"""

import geni.portal as portal
import geni.rspec.pg as pg
import geni.rspec.emulab as emulab

pc = portal.Context()
request = pc.makeRequestRSpec()

# -------------------------------------------------------------------
# 1) Top-level parameters (no assumptions about max nodes)
# -------------------------------------------------------------------

pc.defineParameter(
    "nodeCount", "Number of Nodes", portal.ParameterType.INTEGER, 9,
    longDescription="If you specify more than one node, we will create a LAN for you."
)

pc.defineParameter(
    "sameOS", "Use same OS for all nodes", portal.ParameterType.BOOLEAN, True,
    longDescription="Uncheck to pick a different OS image for each node."
)

pc.defineParameter(
    "sameHardwareType", "Use same hardware type for all nodes",
    portal.ParameterType.BOOLEAN, True,
    longDescription="Uncheck to pick a different hardware type for each node."
)

# The rest of your unchanged parameters:
pc.defineParameter("useVMs",  "Use XEN VMs", portal.ParameterType.BOOLEAN, False,
                   longDescription="Create XEN VMs instead of allocating bare metal nodes.")
pc.defineParameter("startVNC",  "Start X11 VNC on your nodes", portal.ParameterType.BOOLEAN, False,
                   longDescription="Start X11 VNC server on your nodes; a menu option will appear.")
pc.defineParameter("linkSpeed", "Link Speed", portal.ParameterType.INTEGER, 0,
                   [(0, "Any"), (100000, "100Mb/s"), (1000000, "1Gb/s"),
                    (10000000, "10Gb/s"), (25000000, "25Gb/s"), (100000000, "100Gb/s")],
                   advanced=True,
                   longDescription="Optional specific link speed for your LAN.")
pc.defineParameter("bestEffort",  "Best Effort", portal.ParameterType.BOOLEAN, False,
                   advanced=True,
                   longDescription="Ignore bandwidth constraints for very large LANs.")
pc.defineParameter("sameSwitch",  "No Interswitch Links", portal.ParameterType.BOOLEAN, False,
                   advanced=True,
                   longDescription="Force all nodes on the same switch (may prevent mapping).")
pc.defineParameter("tempFileSystemSize", "Temporary Filesystem Size",
                   portal.ParameterType.INTEGER, 0, advanced=True,
                   longDescription="GB of temporary storage (deleted on teardown).")
pc.defineParameter("tempFileSystemMax",  "Temp Filesystem Max Space",
                   portal.ParameterType.BOOLEAN, False, advanced=True,
                   longDescription="Allocate all available disk space instead of specifying a size.")
pc.defineParameter("tempFileSystemMount", "Temporary Filesystem Mount Point",
                   portal.ParameterType.STRING, "/mydata", advanced=True,
                   longDescription="Mount point for the temporary filesystem.")

# -------------------------------------------------------------------
# 2) Bind the toggles & nodeCount, then generate dynamic parameters
# -------------------------------------------------------------------

initial_params = pc.bindParameters()

# list of images for all selectors
imageList = [
    ('default',   'Default Image'),
    ('urn:publicid:IDN+cloudlab.umass.edu+image+sfcs-PG0:ztx_ubuntu22',   'UBUNTU 22.04 ZTX'),
    ('urn:publicid:IDN+cloudlab.umass.edu+image+sfcs-PG0:p4_sdn',        'P4-SDN UBUNTU22'),
    ('urn:publicid:IDN+cloudlab.umass.edu+image+sfcs-PG0:BG_QOE_PRED_P4_SDN','QOE-PRED-P4-SDN'),
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU22-64-STD',     'UBUNTU22-64-STD'),
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU24-64-BETA',    'UBUNTU24-64-BETA'),
    ('urn:publicid:IDN+cloudlab.umass.edu+image+sfcs-PG0:ubuntu24lts',    'UBUNTU 24.04 LTS'),
    ('urn:publicid:IDN+utah.cloudlab.us+image+sfcs-PG0:sfc_u20_k8s_5g_uth','UBUNTU 20.04 K8s 5G Utah'),
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU18-64-STD',     'UBUNTU 18.04'),
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU22-64-ARM',     'UBUNTU22-64-ARM'),
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU20-64-STD',     'UBUNTU 20.04'),
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU16-64-STD',     'UBUNTU 16.04'),
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//CENTOS7-64-STD',      'CENTOS 7'),
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//FBSD112-64-STD',      'FreeBSD 11.2'),
]

# Global OS selector: visible only when sameOS=True
pc.defineParameter(
    "osImage", "Select OS image (global)", portal.ParameterType.IMAGE,
    imageList[1], imageList,
    longDescription="If using the same OS for every node, pick it here.",
    advanced=not initial_params.sameOS
)

# Per-node OS selectors: visible only when sameOS=False
for i in range(initial_params.nodeCount):
    pc.defineParameter(
        "osImage_%d" % i,
        "OS image for node %d" % (i + 1),
        portal.ParameterType.IMAGE,
        imageList[1], imageList,
        longDescription="Select OS image for node %d" % (i + 1),
        advanced=initial_params.sameOS
    )

# Global hardware-type selector: visible only when sameHardwareType=True
pc.defineParameter(
    "phystype", "Select hardware type (global)", portal.ParameterType.NODETYPE,
    "",
    longDescription="If using the same hardware for every node, pick it here.",
    advanced=not initial_params.sameHardwareType
)

# Per-node hardware selectors: visible only when sameHardwareType=False
for i in range(initial_params.nodeCount):
    pc.defineParameter(
        "phystype_%d" % i,
        "Hardware type for node %d" % (i + 1),
        portal.ParameterType.NODETYPE,
        "",
        longDescription="Select hardware type for node %d" % (i + 1),
        advanced=initial_params.sameHardwareType
    )

# -------------------------------------------------------------------
# 3) Final bind, validation, and RSpec assembly
# -------------------------------------------------------------------

params = pc.bindParameters()

# Basic validations
if params.nodeCount < 1:
    pc.reportError(portal.ParameterError("You must choose at least 1 node.", ["nodeCount"]))
if params.tempFileSystemSize < 0 or params.tempFileSystemSize > 200:
    pc.reportError(portal.ParameterError(
        "Please specify a size greater than zero and less than 200GB.",
        ["tempFileSystemSize"]
    ))
# global phystype must remain a single token (if used)
if params.phystype:
    if len(params.phystype.split(",")) != 1:
        pc.reportError(portal.ParameterError("Only a single type is allowed", ["phystype"]))

pc.verifyParameters()

# Build LAN if needed
if params.nodeCount > 1:
    if params.nodeCount == 2:
        lan = request.Link()
    else:
        lan = request.LAN()
    if params.bestEffort:
        lan.best_effort = True
    elif params.linkSpeed > 0:
        lan.bandwidth = params.linkSpeed
    if params.sameSwitch:
        lan.setNoInterSwitchLinks()

# Instantiate each node
for i in range(params.nodeCount):
    name = "vm%d" % i if params.useVMs else "node%d" % i
    node = request.XenVM(name) if params.useVMs else request.RawPC(name)

    # OS assignment
    if params.sameOS:
        if params.osImage and params.osImage != "default":
            node.disk_image = params.osImage
    else:
        choice = getattr(params, "osImage_%d" % i)
        if choice and choice != "default":
            node.disk_image = choice

    # Attach to LAN
    if params.nodeCount > 1:
        iface = node.addInterface("eth1")
        lan.addInterface(iface)

    # Hardware assignment
    if params.sameHardwareType:
        if params.phystype:
            node.hardware_type = params.phystype
    else:
        choice = getattr(params, "phystype_%d" % i)
        if choice:
            node.hardware_type = choice

    # Optional blockstore
    if params.tempFileSystemSize > 0 or params.tempFileSystemMax:
        bs = node.Blockstore("%s-bs" % name, params.tempFileSystemMount)
        bs.size = "0GB" if params.tempFileSystemMax else "%dGB" % params.tempFileSystemSize
        bs.placement = "any"

    # VNC if requested
    if params.startVNC:
        node.startVNC()

pc.printRequestRSpec(request)
