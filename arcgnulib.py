#!/usr/bin/env python3

# Copyright (c) 2026, Synopsys, Inc. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1) Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2) Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# 3) Neither the name of the Synopsys, Inc., nor the names of its contributors
# may be used to endorse or promote products derived from this software
# without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import logging
import os.path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional


class TCF:
    def __init__(self, filename: str, no_compressed: bool = False):
        self._filename = filename
        self._no_compressed = no_compressed
        self._init_root_node()
        self._init_compile_options()
        self._init_memory_options()

    def _init_root_node(self):
        try:
            self._tree = ET.parse(self._filename)
            logging.debug("opened TCF: %s", self._filename)
        except FileNotFoundError:
            logging.error('File "%s" is not found.', self._filename)
            sys.exit(1)

        self._root_node = self._tree.getroot()

    def _init_compile_options(self):
        # Extract compile options
        options_node = self._root_node.find("./configuration[@name='gcc_compiler']/string")

        if options_node is None:
            logging.error("gcc_compiler configuration is not found.")
            sys.exit(1)

        self._compile_options_list = []
        compile_options_list_raw = [option.strip() for option in options_node.text.split()]

        # Generate -march, -mtune and -mabi
        self._march = None
        self._mtune = None
        self._mabi = None
        self._mcmodel = "medlow"

        for option in compile_options_list_raw:
            if option.startswith("-march="):
                self._march = option.split("=")[1].lower()
                if self._no_compressed:
                    candidates = ["c", "zca", "zcb", "zcf", "zcd", "zcmp", "zcmt"]
                    extensions = self.get_extensions()
                    extensions = list(filter(lambda x: x not in candidates, extensions))
                    self._march = "_".join(extensions)
                option = "-march=" + self._march
            elif option.startswith("-mtune="):
                self._mtune = option.split("=")[1].lower()
            elif option.startswith("-mabi="):
                self._mabi = option.split("=")[1].lower()
            self._compile_options_list.append(option)

        if self._march is None:
            logging.error("-march is not found in TCF.")
            sys.exit(1)

        if self._mtune is None:
            logging.error("-mtune is not found in TCF.")
            sys.exit(1)

        if self._mabi is None:
            logging.error("-mabi is not found in TCF.")
            sys.exit(1)

        # Generate -mcmodel for RV64 targets
        if "rv64" in self._march:
            self._mcmodel = "medany"

        logging.debug("compile options extracted: %s", str(self._compile_options_list))

    def _init_memory_options(self):
        # Extract ICCM and DCCM configurations
        self._memory_options_list = []
        nsim_node = self._root_node.find("./configuration[@name='nSIM']/string")

        if nsim_node is None:
            logging.error("nSIM configuration is not found.")
            sys.exit(1)

        nsim_options_map = {}
        for nsim_option in nsim_node.text.split():
            key, value = nsim_option.strip().split("=", maxsplit=1)
            nsim_options_map[key] = value

        # Newlib/Picolibc toolchains and nSIM use different symbols
        # for .text and .data sections:
        #
        #     Section          Newlib          Picolibc        nSIM
        #     .text address    txtmem_addr     __flash         iccm0_base
        #     .text size       txtmem_len      __flash_size    iccm0_size
        #     .data address    datamem_addr    __ram           dccm_base
        #     .data size       datamem_len     __ram_size      dccm_size
        self._iccm_base = nsim_options_map.get("iccm0_base", None)
        if self._iccm_base is not None:
            self._memory_options_list.append("-Wl,-defsym=txtmem_addr={}".format(self._iccm_base))
            self._memory_options_list.append("-Wl,-defsym=__flash={}".format(self._iccm_base))

        self._iccm_size = nsim_options_map.get("iccm0_size", None)
        if self._iccm_size is not None:
            self._memory_options_list.append("-Wl,-defsym=txtmem_len={}".format(self._iccm_size))
            self._memory_options_list.append("-Wl,-defsym=__flash_size={}".format(self._iccm_size))

        self._dccm_base = nsim_options_map.get("dccm_base", None)
        if self._dccm_base is not None:
            self._memory_options_list.append("-Wl,-defsym=datamem_addr={}".format(self._dccm_base))
            self._memory_options_list.append("-Wl,-defsym=__ram={}".format(self._dccm_base))

        self._dccm_size = nsim_options_map.get("dccm_size", None)
        if self._dccm_size is not None:
            self._memory_options_list.append("-Wl,-defsym=datamem_len={}".format(self._dccm_size))
            self._memory_options_list.append("-Wl,-defsym=__ram_size={}".format(self._dccm_size))

        logging.debug("memory options extracted: %s", str(self._memory_options_list))

    def get_march(self) -> str:
        return self._march

    def get_family(self) -> str:
        for family in "rv32i", "rv32e", "rv64i":
            if self._march.startswith(family):
                return family

        raise ValueError("march does not start with a correct family")

    def get_extensions(self) -> list[str]:
        family = self.get_family()
        march = self._march[len(family) :]
        extensions = [family]

        for extension in march.split("_"):
            extension = extension.replace("_", "")
            if len(extension) == 0:
                continue
            if extension[0] in ("z", "x"):
                extensions.append(extension)
            else:
                extensions.extend(list(extension))

        return extensions

    def get_mabi(self) -> str:
        return self._mabi

    def get_mtune(self) -> str:
        return self._mtune

    def get_mcmodel(self) -> str:
        return self._mcmodel

    def get_iccm_base(self) -> Optional[str]:
        return self._iccm_base

    def get_iccm_size(self) -> Optional[str]:
        return self._iccm_size

    def get_dccm_base(self) -> Optional[str]:
        return self._dccm_base

    def get_dccm_size(self) -> Optional[str]:
        return self._dccm_size

    def get_compile_options(self) -> list[str]:
        return self._compile_options_list.copy()

    def get_memory_options(self) -> list[str]:
        return self._memory_options_list.copy()


class CompilerInfo:
    def __init__(self, compiler_filename: str):
        # Try to locate a path to GCC binary
        self._compiler_name = compiler_filename
        self._compiler_path = shutil.which(self._compiler_name)
        logging.info("Trying to locate a tool: %s", self._compiler_name)

        if self._compiler_path:
            logging.info("Found GCC in PATH: %s", self._compiler_path)
        else:
            self._compiler_path = Path(__file__).parent / self._compiler_name
            if self._compiler_path.exists():
                logging.info("Found GCC in a local directory: %s", str(self._compiler_path))
                self._compiler_path = str(self._compiler_path)
            else:
                logging.error("Cannot find GCC in PATH or in a local directory.")
                sys.exit(1)

        # Try to determine a real GCC triplet. Original script name may be
        # an alias to a real GCC binary with correct triplet. We can determine
        # a real GCC triplet only through -dumpmachine option.
        try:
            result = subprocess.run([self._compiler_path, "-dumpmachine"], capture_output=True, encoding="utf-8")
            if result.returncode != 0:
                logging.error("Cannot retrieve a triplet from GCC:\n%s", result.stderr)
                sys.exit(1)
            self._compiler_triplet = result.stdout.strip()
            logging.info("Retrieved a real triplet of GCC: %s", self._compiler_triplet)
        except FileNotFoundError:
            logging.error("GCC path is invalid: %s", self._compiler_path)
            sys.exit(1)

    def get_compiler_name(self) -> str:
        return self._compiler_name

    def get_compiler_path(self) -> str:
        return self._compiler_path

    def get_compiler_triplet(self) -> str:
        return self._compiler_triplet
