# Copyright 2013 Daniel Narvaez
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import json
import os
import subprocess

from mmake import sourcestamp


def pull(base_dir, modules):
    for module_name in modules.keys():
        os.chdir(base_dir)
        subprocess.check_call("git submodule update --init %s" % module_name,
                              shell=True)


def clean(base_dir, modules):
    os.chdir(base_dir)
    subprocess.check_call("git clean -fdx", shell=True)

    for module_name in modules.keys():
        os.chdir(os.path.join(base_dir, module_name))
        subprocess.check_call("git clean -fdx", shell=True)


def resolve_deps(modules):
    sorted_nodes = []

    graph_unsorted = {}
    for name, info in modules.items():
        graph_unsorted[name] = info.get("deps", [])

    while graph_unsorted:
        acyclic = False
        for node, edges in graph_unsorted.items():
            for edge in edges:
                if edge in graph_unsorted:
                    break
            else:
                acyclic = True
                del graph_unsorted[node]
                sorted_nodes.append(node)

        if not acyclic:
            raise RuntimeError("A cyclic dependency occurred")

    return sorted_nodes


def build(base_dir, modules):
    stamps_dir = os.path.join(base_dir, "build", "stamps")

    try:
        os.mkdir(stamps_dir)
    except OSError:
        pass

    install_dir = os.path.join(base_dir, "build", "install")
    lib_dir = os.path.join(install_dir, "lib")
    share_dir = os.path.join(install_dir, "share")

    pkgconfig_dirs = [os.path.join(share_dir, "pkgconfig"),
                      os.path.join(lib_dir, "pkgconfig")]

    aclocal_dir = os.path.join(share_dir, "aclocal")

    try:
        os.makedirs(aclocal_dir)
    except OSError:
        pass

    os.environ["INSTALL_DIR"] = install_dir
    os.environ["LD_LIBRARY_PATH"] = lib_dir
    os.environ["PKG_CONFIG_PATH"] = ":".join(pkgconfig_dirs)
    os.environ["ACLOCAL"] = "aclocal -I %s" % aclocal_dir

    for module_name in resolve_deps(modules):
        module_info = modules[module_name]

        source_dir = os.path.join(base_dir, module_name)
        recipe_path = os.path.join(base_dir, module_info["build"])
        stamp_path = os.path.join(stamps_dir, module_name)

        try:
            with open(stamp_path) as f:
                old_stamp = f.read()
        except IOError:
            old_stamp = None

        new_stamp = sourcestamp.compute(source_dir)
        if old_stamp != new_stamp:
            os.environ["SOURCE_DIR"] = source_dir

            os.chdir(source_dir)
            subprocess.check_call(["sh", recipe_path])

        with open(stamp_path, "w") as f:
            f.write(sourcestamp.compute(source_dir))


def run():
    base_dir = os.getcwd()

    with open(os.path.join(base_dir, "manifest.json")) as f:
        modules = json.load(f)

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("build")
    subparsers.add_parser("pull")
    subparsers.add_parser("clean")

    args = parser.parse_args()
    if args.command == "build":
        build(base_dir, modules)
    elif args.command == "clean":
        clean(base_dir, modules)
    elif args.command == "pull":
        pull(base_dir, modules)
