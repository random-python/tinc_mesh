#!/usr/bin/env python

#
# generate public/secret keys for local node in tinc.conf
#

import os

this_dir = os.path.dirname(os.path.abspath(__file__))

os.system(f"rm -f {this_dir}/rsa_key.priv")
os.system(f"tincd --config={this_dir} --generate-keys")
os.system(f"chmod -R go-rwx {this_dir}")
