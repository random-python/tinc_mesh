"""
mesh network operations

https://www.tinc-vpn.org/

note on naming:
* 'host' means own declared node from /etc/tinc/mesh/tinc.conf
* 'hosts' means configured nodes from /etc/tinc/mesh/hosts/<host>
* 'nodes' means discovered nodes from /etc/tinc/mesh/nodes/<node>
"""

import os
import shlex
import logging
import subprocess
from datetime import datetime
from typing import Mapping, List, Callable

logging.basicConfig(
    level='INFO',
)

logger = logging.getLogger(__name__)


def invoke_shell(script) -> subprocess.CompletedProcess:
    return subprocess.check_output(script, shell=True)


def parse_conf_list(line_list:List[str]) -> Mapping[str, str]:
    "extract key=value from list as dict"
    conf_dict = dict()
    for line in line_list:
        if '=' in line:
            key, value = line.partition("=")[::2]
            key = key.lower().strip()  # cased to lower
            value = value.strip()  # keep case
            conf_dict[key] = value
    return conf_dict


def parse_conf_text(conf_text:str, separator:str='\n') -> Mapping[str, str]:
    "extract key=value from text as dict"
    line_list = conf_text.split(separator)
    return parse_conf_list(line_list)


def parse_conf_file(conf_file:str) -> Mapping[str, str]:
    "extract key=value from file.conf as dict"
    with open(conf_file, "r") as line_list:
        return parse_conf_list(line_list)


def tinker_etc_dir() -> str:
    "mesh network setttings folder"
    etc_dir = os.getenv('TINKER_ETC_DIR', '/etc/tinc')
    return etc_dir


def tinker_mesh_dir() -> str:
    "mesh network settings folder"
    mesh_dir = os.getenv('TINKER_NET_NAME', 'mesh')
    return f"{tinker_etc_dir()}/{mesh_dir}"


def tinker_conf_file() -> str:
    "mesh network setttings file"
    conf_file = os.getenv('TINKER_CONF_FILE', 'tinc.conf')
    return f"{tinker_mesh_dir()}/{conf_file}"


def tinker_conf_dict() -> Mapping[str, str]:
    "extract /etc/tinc/mesh/tinc.conf as dict"
    return parse_conf_file(tinker_conf_file())


def tinker_host_dir() -> str:
    "hosts provided by mesh configuration"
    host_dir = os.getenv('TINKER_HOST_BASE', 'hosts')
    return f"{tinker_mesh_dir()}/{host_dir}"


def tinker_host_file(host_name:str) -> str:
    "configured host file: /etc/tinc/mesh/hosts/<host>"
    host_dir = tinker_host_dir()
    host_file = f"{host_dir}/{host_name}"
    return host_file


def tinker_host_conf(host_name:str) -> Mapping[str, str]:
    "extract host config /etc/tinc/mesh/hosts/<host> as dict"
    host_file = tinker_host_file(host_name)
    return parse_conf_file(host_file)


def tinker_node_dir() -> str:
    "active nodes set by up/down script"
    node_dir = os.getenv('TINKER_NODE_BASE', 'nodes')
    return f"{tinker_mesh_dir()}/{node_dir}"


def tinker_node_file(node_name:str) -> str:
    "active nodes set by up/down script"
    node_dir = tinker_node_dir()
    return f"{node_dir}/{node_name}"


def tinker_node_conf(node_name:str) -> Mapping[str, str]:
    "extract /etc/tinc/mesh/nodes/<node> as dict"
    node_file = tinker_node_file(node_name)
    return parse_conf_file(node_file)


def tinker_host_name() -> str:
    "own node name from /etc/tinc/mesh/tinc.conf"
    conf_dict = tinker_conf_dict()
    return conf_dict['name']  # cased to lower


def tinker_host_subnet() -> str:
    "own node subnet from /etc/tinc/mesh/hosts/<self>"
    host_name = tinker_host_name()
    host_dict = tinker_host_conf(host_name)
    host_subnet = host_dict['subnet']  # cased to lower
    return host_subnet


def tinker_host_network() -> str:
    "own node network from /etc/tinc/mesh/hosts/<self>"
    host_subnet = tinker_host_subnet()
    assert '/' in  host_subnet, f"need proper subnet: {host_subnet}"
    subnet_term = host_subnet.split('/', 1)
    host_addr = subnet_term[0]
    host_mask = subnet_term[1]
    assert host_mask == '32', f"need single address subnet: {host_subnet}"
    host_network = f"{host_addr}/24"  # expand mask one level up
    return host_network


def tinker_skip_list() -> List[str]:
    "list of host names excluded from node iteration"
    skip_list = os.environ.get('TINKER_SKIP_LIST', (
        'readme.md "readme.txt" readme.rst'
    ))
    return shlex.split(skip_list)


def tinker_node_list() -> List[str]:
    "extract active node name list, except for self node"
    node_dir = tinker_node_dir()
    if not os.path.isdir(node_dir):
        return list()
    host_name = tinker_host_name()  # self node
    skip_list = [host_name] + tinker_skip_list()
    node_list = [
        entry for entry in os.listdir(node_dir)
        if entry not in skip_list
    ]
    node_list.sort()
    return node_list


def tinker_node_iterate(node_func:Callable) -> None:
    "apply function on live node list"
    node_list = tinker_node_list()
    logger.debug(f"node_list: {node_list}")
    for node_name in node_list:
        conf_dict = tinker_node_conf(node_name)
        node_addr = conf_dict['node_addr']  # from up/down script
        func_name = node_func.__name__
        func_info = f"{func_name} :: {node_name} {node_addr}"
        try:
            node_func(node_name, node_addr)
        except Exception as error:
            logger.warn(f"failure: {func_info} :: {error}")


def tinker_script_node() -> str:
    "node provided by tincd on up/down"
    return os.environ.get('NODE', None)


def tinker_script_netname() -> str:
    "net name provided by tincd on up/down"
    return os.environ.get('NETNAME', None)


def tinker_script_subnet() -> str:
    "subnet provided by tincd on up/down"
    return os.environ.get('SUBNET', None)


def tinker_script_device() -> str:
    "interface provided by tincd on up/down"
    return os.environ.get('INTERFACE', None)


def tinker_script_addr() -> str:
    "address provided by tincd on up/down"
    tinc_subnet = tinker_script_subnet()
    subnet_term = tinc_subnet.split('/', 1)
    subnet_addr = subnet_term[0]
    subnet_mask = subnet_term[1]
    return subnet_addr


def tinker_script_tinc_up() -> None:
    "invoked from /etc/tinc/mesh/tinc-up"
    "configure vpn network"
    node_dir = tinker_node_dir()
    tinc_device = tinker_script_device()
    tinc_netname = tinker_script_netname()
    tinc_network = tinker_host_network()
    logger.info(f"tinc startup: {tinc_netname} {tinc_network}")
    invoke_shell(f"""
        mkdir -p "{node_dir}"
        ip link set {tinc_device} up
        ip addr add {tinc_network} dev {tinc_device}
    """)


def tinker_script_tinc_down() -> None:
    "invoked from /etc/tinc/mesh/tinc-down"
    "unconfigure vpn network"
    node_dir = tinker_node_dir()
    tinc_device = tinker_script_device()
    tinc_netname = tinker_script_netname()
    tinc_network = tinker_host_network()
    logger.info(f"tinc shutdown: {tinc_netname} {tinc_network}")
    invoke_shell(f"""
        ip addr del {tinc_network} dev {tinc_device}
        ip link set {tinc_device} down
        rm -rf "{node_dir}"
    """)


def tinker_script_subnet_up() -> None:
    "invoked from /etc/tinc/mesh/subnet-up"
    "create node conf file"
    node_name = tinker_script_node()
    node_file = tinker_node_file(node_name)
    node_addr = tinker_script_addr()
    node_time = datetime.now().isoformat()
    logger.info(f"subnet create: {node_name} {node_addr}")
    with open(node_file, "w") as node_conf:
        node_conf.write(f"node_name={node_name}\n")
        node_conf.write(f"node_addr={node_addr}\n")
        node_conf.write(f"node_time={node_time}\n")


def tinker_script_subnet_down() -> None:
    "invoked from /etc/tinc/mesh/subnet-down"
    "delete node conf file"
    node_name = tinker_script_node()
    node_file = tinker_node_file(node_name)
    logger.info(f"subnet delete: {node_name}")
    if os.path.isfile(node_file):
        os.remove(node_file)
