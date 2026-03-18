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
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

class TCFError(Exception):
    pass

class TCFCompilerConfigurationNotFoundError(TCFError):
    pass

class TCFMemoryConfigurationNotFoundError(TCFError):
    pass

class TCFTargetOptionError(TCFError):
    pass

class TCF:
    COMPRESSED_EXTENSIONS = ["c", "zca", "zcb", "zcf", "zcd", "zcmp", "zcmt"]

    def __init__(self, content: str):
        self._root_node = ET.fromstring(content)
        self._init_compile_options()
        self._init_march_no_compressed()
        self._init_memory_options()

    @classmethod
    def from_file(cls, filename: str, *args, **kwargs):
        """Create a TCF instance from a file.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        logging.debug("Opening TCF: %s", filename)
        with open(filename, "rb") as f:
            content = f.read()
            return cls(content, *args, **kwargs)

    def _init_compile_options(self):
        # Extract compile options
        options_node = self._root_node.find("./configuration[@name='gcc_compiler']/string")

        if options_node is None:
            raise TCFCompilerConfigurationNotFoundError("gcc_compiler configuration is not found.")

        cflags = [option.strip() for option in options_node.text.split()]

        # Generate -march, -mtune, -mabi and -mcmodel values
        self._march = None
        self._march_family = None
        self._mtune = None
        self._mabi = None
        self._mcmodel = "medlow"
        self._extra_cflags = []

        for option in cflags:
            if option.startswith("-march="):
                self._march = option.split("=")[1].lower()
                option = "-march=" + self._march
            elif option.startswith("-mtune="):
                self._mtune = option.split("=")[1].lower()
            elif option.startswith("-mabi="):
                self._mabi = option.split("=")[1].lower()
            else:
                self._extra_cflags.append(option)

        if self._march is None:
            raise TCFTargetOptionError("-march is not found in TCF.")

        for family in "rv32i", "rv32e", "rv64i":
            if self._march.startswith(family):
                self._march_family = family
                break
        else:
            raise TCFTargetOptionError("march does not start with a correct family: {}".format(self._march))

        if self._mtune is None:
            raise TCFTargetOptionError("-mtune is not found in TCF.")

        if self._mabi is None:
            raise TCFTargetOptionError("-mabi is not found in TCF.")

        # Generate -mcmodel for RV64 targets
        if "rv64" in self._march:
            self._mcmodel = "medany"

    def _init_march_no_compressed(self):
        march_extensions = self._get_march_extensions()
        filtered = list(filter(lambda x: x not in self.COMPRESSED_EXTENSIONS, march_extensions))
        self._march_no_compressed = "_".join([
            self._march_family,
            *filtered,
        ])

    def _get_march_extensions(self) -> list[str]:
        march_extensions_str = self._march[len(self._march_family):]
        march_extensions = []

        for extension in march_extensions_str.split("_"):
            extension = extension.replace("_", "")
            if len(extension) == 0:
                continue
            if extension[0] in ("z", "x"):
                march_extensions.append(extension)
            else:
                march_extensions.extend(list(extension))

        return march_extensions

    def _init_memory_options(self):
        # Extract ICCM and DCCM configurations
        self._memory_options_list = []
        nsim_node = self._root_node.find("./configuration[@name='nSIM']/string")

        if nsim_node is None or nsim_node.text is None:
            raise TCFMemoryConfigurationNotFoundError("nSIM configuration is not found.")

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

    def get_march(self, no_compressed: bool = False) -> str:
        if no_compressed:
            return self._march_no_compressed

        return self._march

    def get_family(self) -> str:
        return self._march_family

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

    def get_compile_options(self, no_compressed: bool = False) -> list[str]:
        return [
            "-march={}".format(self.get_march(no_compressed)),
            "-mtune={}".format(self.get_mtune()),
            "-mabi={}".format(self.get_mabi()),
            "-mcmodel={}".format(self.get_mcmodel()),
            *self._extra_cflags,
        ]

    def get_memory_options(self) -> list[str]:
        return self._memory_options_list.copy()

class CompilerInfoGCCNotFoundError(Exception):
    pass

class CompilerInfoGCCExecutionError(Exception):
    pass

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
                raise CompilerInfoGCCNotFoundError("Cannot find GCC in PATH or in a local directory.")

        # Try to determine a real GCC triplet. Original script name may be
        # an alias to a real GCC binary with correct triplet. We can determine
        # a real GCC triplet only through -dumpmachine option.
        try:
            result = subprocess.run([self._compiler_path, "-dumpmachine"], capture_output=True, encoding="utf-8", check=True)
            self._compiler_triplet = result.stdout.strip()
            logging.info("Retrieved a real triplet of GCC: %s", self._compiler_triplet)
        except subprocess.CalledProcessError as exc:
            raise CompilerInfoGCCExecutionError("Cannot retrieve a triplet from GCC:\n{}".format(exc.stderr)) from exc
        except FileNotFoundError as exc:
            raise CompilerInfoGCCNotFoundError("GCC path is invalid: {}".format(self._compiler_path)) from exc

    def get_compiler_name(self) -> str:
        return self._compiler_name

    def get_compiler_path(self) -> str:
        return self._compiler_path

    def get_compiler_triplet(self) -> str:
        return self._compiler_triplet
