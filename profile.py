"""Variable number of nodes in a lan. You have the option of picking from one
of several standard images we provide, or just use the default (typically a recent
version of Ubuntu). You may also optionally pick the specific hardware type for
all the nodes in the lan. 

Instructions:
Wait for the experiment to start, and then log into one or more of the nodes
by clicking on them in the toplogy, and choosing the `shell` menu option.
Use `sudo` to run root commands. 
"""

# Import the Portal object.
import geni.portal as portal
# Import the ProtoGENI library.
import geni.rspec.pg as pg
# Emulab specific extensions.
import geni.rspec.emulab as emulab

# Create a portal context, needed to defined parameters
pc = portal.Context()

# Create a Request object to start building the RSpec.
request = pc.makeRequestRSpec()

# Variable number of nodes.
pc.defineParameter("nodeCount", "Number of Nodes", portal.ParameterType.INTEGER, 9,
                   longDescription="If you specify more then one node, " +
                   "we will create a lan for you.")

# Pick your OS.
imageList = [
    ('default', 'Default Image'),
    ('urn:publicid:IDN+cloudlab.umass.edu+image+sfcs-PG0:ztx_ubuntu22', 'UBUNTU 22.04 ZTX'),
    ('urn:publicid:IDN+cloudlab.umass.edu+image+sfcs-PG0:p4_sdn', 'P4-SDN UBUNTU22'),
    ('urn:publicid:IDN+cloudlab.umass.edu+image+sfcs-PG0:BG_QOE_PRED_P4_SDN', 'QOE-PRED-P4-SDN'),
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU22-64-STD', 'UBUNTU22-64-STD'),
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU24-64-BETA', 'UBUNTU24-64-BETA'),
    ('urn:publicid:IDN+cloudlab.umass.edu+image+sfcs-PG0:ubuntu24lts', 'UBUNTU 24.04 LTS'),
    ('urn:publicid:IDN+utah.cloudlab.us+image+sfcs-PG0:sfc_u20_k8s_5g_uth', 'UBUNTU 20.04 K8s 5G Utah'),
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU18-64-STD', 'UBUNTU 18.04'),
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU22-64-ARM', 'UBUNTU22-64-ARM'),
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU20-64-STD', 'UBUNTU 20.04'),
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU16-64-STD', 'UBUNTU 16.04'),
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//CENTOS7-64-STD',  'CENTOS 7'),
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//FBSD112-64-STD', 'FreeBSD 11.2')]

pc.defineParameter("osImage", "Select OS image",
                   portal.ParameterType.IMAGE,
                   imageList[1], imageList,
                   longDescription="Most clusters have this set of images, " +
                   "pick your favorite one.")

# <<< added: allow per-node OS choice
pc.defineParameter("sameOS", "Use same OS for all nodes", portal.ParameterType.BOOLEAN, True,
                   longDescription="If checked, use the single OS image above for every node. "
                                   "Otherwise specify a comma-separated list of image URNs.")
pc.defineParameter("osImageList", "Comma-separated OS image URNs", portal.ParameterType.STRING, "",
                   longDescription="List of OS image URNs for each node if not using the same OS.")

# Optional physical type for all nodes.
pc.defineParameter("phystype",  "Optional physical node type",
                   portal.ParameterType.NODETYPE, "",
                   longDescription="Specify a physical node type (pc3000,d710,etc) " +
                   "instead of letting the resource mapper choose for you.")

# <<< added: allow per-node hardware choice
pc.defineParameter("sameHardwareType", "Use same hardware type for all nodes", portal.ParameterType.BOOLEAN, True,
                   longDescription="If checked, use the single hardware type above for every node. "
                                   "Otherwise specify a comma-separated list of types.")
pc.defineParameter("hardwareTypeList", "Comma-separated hardware types", portal.ParameterType.STRING, "",
                   longDescription="List of hardware types for each node if not using the same type.")

# Optional root filesystem size
#pc.defineParameter("rootFileSystemSize", "Root Filesystem Size",
#                   portal.ParameterType.INTEGER, 0,
#                   longDescription="The size in GB of a root file system to mount on each of your " +
#                   "nodes. 0 means maximum possible space is allocated.")

# Optionally create XEN VMs instead of allocating bare metal nodes.
pc.defineParameter("useVMs",  "Use XEN VMs",
                   portal.ParameterType.BOOLEAN, False,
                   longDescription="Create XEN VMs instead of allocating bare metal nodes.")

# Optionally start X11 VNC server.
pc.defineParameter("startVNC",  "Start X11 VNC on your nodes",
                   portal.ParameterType.BOOLEAN, False,
                   longDescription="Start X11 VNC server on your nodes. There will be " +
                   "a menu option in the node context menu to start a browser based VNC " +
                   "client. Works really well, give it a try!")

# Optional link speed, normally the resource mapper will choose for you based on node availability
pc.defineParameter("linkSpeed", "Link Speed", portal.ParameterType.INTEGER, 0,
                   [(0, "Any"), (100000, "100Mb/s"), (1000000, "1Gb/s"), (10000000,
                                                                          "10Gb/s"), (25000000, "25Gb/s"), (100000000, "100Gb/s")],
                   advanced=True,
                   longDescription="A specific link speed to use for your lan. Normally the resource " +
                   "mapper will choose for you based on node availability and the optional physical type.")

# For very large lans you might to tell the resource mapper to override the bandwidth constraints
# and treat it a "best-effort"
pc.defineParameter("bestEffort",  "Best Effort", portal.ParameterType.BOOLEAN, False,
                   advanced=True,
                   longDescription="For very large lans, you might get an error saying 'not enough bandwidth.' " +
                   "This options tells the resource mapper to ignore bandwidth and assume you know what you " +
                   "are doing, just give me the lan I ask for (if enough nodes are available).")

# Sometimes you want all of nodes on the same switch, Note that this option can make it impossible
# for your experiment to map.
pc.defineParameter("sameSwitch",  "No Interswitch Links", portal.ParameterType.BOOLEAN, False,
                    advanced=True,
                    longDescription="Sometimes you want all the nodes connected to the same switch. " +
                    "This option will ask the resource mapper to do that, although it might make " +
                    "it imppossible to find a solution. Do not use this unless you are sure you need it!")

# Optional ephemeral blockstore
pc.defineParameter("tempFileSystemSize", "Temporary Filesystem Size",
                   portal.ParameterType.INTEGER, 0, advanced=True,
                   longDescription="The size in GB of a temporary file system to mount on each of your " +
                   "nodes. Temporary means that they are deleted when your experiment is terminated. " +
                   "The images provided by the system have small root partitions, so use this option " +
                   "if you expect you will need more space to build your software packages or store " +
                   "temporary files.")

# Instead of a size, ask for all available space.
pc.defineParameter("tempFileSystemMax",  "Temp Filesystem Max Space",
                   portal.ParameterType.BOOLEAN, False,
                   advanced=True,
                   longDescription="Instead of specifying a size for your temporary filesystem, " +
                   "check this box to allocate all available disk space. Leave the size above as zero.")

pc.defineParameter("tempFileSystemMount", "Temporary Filesystem Mount Point",
                   portal.ParameterType.STRING, "/mydata", advanced=True,
                   longDescription="Mount the temporary file system at this mount point; in general you " +
                   "you do not need to change this, but we provide the option just in case your software " +
                   "is finicky.")

# Retrieve the values the user specifies during instantiation.
params = pc.bindParameters()

# Check parameter validity.
if params.nodeCount < 1:
    pc.reportError(portal.ParameterError(
        "You must choose at least 1 node.", ["nodeCount"]))

if params.tempFileSystemSize < 0 or params.tempFileSystemSize > 200:
    pc.reportError(portal.ParameterError("Please specify a size greater then zero and " +
                                         "less then 200GB", ["nodeCount"]))

if params.phystype != "":
    tokens = params.phystype.split(",")
    if len(tokens) != 1:
        pc.reportError(portal.ParameterError("Only a single type is allowed", ["phystype"]))

# <<< added: validate per-node hardware list
if not params.sameHardwareType:
    hw_tokens = [t.strip() for t in params.hardwareTypeList.split(",") if t.strip()]
    if len(hw_tokens) != params.nodeCount:
        pc.reportError(portal.ParameterError(
            f"hardwareTypeList must contain {params.nodeCount} entries (comma-separated)", ["hardwareTypeList"]))

# <<< added: validate per-node OS list
if not params.sameOS:
    os_tokens = [o.strip() for o in params.osImageList.split(",") if o.strip()]
    if len(os_tokens) != params.nodeCount:
        pc.reportError(portal.ParameterError(
            f"osImageList must contain {params.nodeCount} entries (comma-separated)", ["osImageList"]))

pc.verifyParameters()

# <<< added: prepare per-node lists
if not params.sameHardwareType:
    hwList = [t.strip() for t in params.hardwareTypeList.split(",")]
else:
    hwList = None

if not params.sameOS:
    osList = [o.strip() for o in params.osImageList.split(",")]
else:
    osList = None

# Create link/lan.
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

# Process nodes, adding to link or lan.
for i in range(params.nodeCount):
    # Create a node and add it to the request
    if params.useVMs:
        name = "vm" + str(i)
        node = request.XenVM(name)
    else:
        name = "node" + str(i)
        node = request.RawPC(name)

    # OS image assignment (per-node or global)
    if osList:
        image = osList[i]
        if image and image != "default":
            node.disk_image = image
    elif params.osImage and params.osImage != "default":
        node.disk_image = params.osImage

    # Add to lan
    if params.nodeCount > 1:
        iface = node.addInterface("eth1")
        lan.addInterface(iface)

    # Hardware type assignment (per-node or global)
    if hwList:
        node.hardware_type = hwList[i]
    elif params.phystype != "":
        node.hardware_type = params.phystype

    # Optional Blockstore
    if params.tempFileSystemSize > 0 or params.tempFileSystemMax:
        bs = node.Blockstore(name + "-bs", params.tempFileSystemMount)
        if params.tempFileSystemMax:
            bs.size = "0GB"
        else:
            bs.size = str(params.tempFileSystemSize) + "GB"
        bs.placement = "any"

    # Install and start X11 VNC if requested
    if params.startVNC:
        node.startVNC()

# Print the RSpec to the enclosing page.
pc.printRequestRSpec(request)
