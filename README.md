# Scripts for GNU Toolchain for ARC-V Targets

This repository contains two useful scripts for the ARC-V GNU toolchain:

1. The `riscv64-snps-elf-tcf-gcc` tool is a TCF wrapper for GCC for ARC-V targets.
   It is intended to be used with TCF files originally prepared for MetaWare tools.
2. The `riscv64-snps-elf-buildlib` tool allows building Picolibc, `libgcc`, and `libstdc++`
   for a particular set of target and optimization options. Then this configuration
   may be used for building applications using the TCF wrapper.

## Installation

Copy all the scripts, including `arcgnulib.py`, to the `bin` directory of a toolchain or add
a directory with the scripts to `PATH`. Note that both scripts try to locate
`riscv64-snps-elf-gcc` in two places:

1. **The same directory where the scripts reside.**
   
   If the scripts' directory contains `riscv64-snps-elf-gcc`, then this binary is used.
2. **A directory in `PATH`.**

Note that the scripts' prefix must match GCC's one. For example, if GCC binary is
`riscv64-unknown-elf-gcc` then scripts must be renamed to
`riscv64-unknown-elf-tcf-gcc` and `riscv64-unknown-elf-buildlib`.

## The TCF wrapper

The TCF Wrapper is a wrapper for GCC from the GNU toolchain for ARC-V that takes target options
from a TCF file and passes them to GCC. The wrapper introduces a list of extra options prefixed with `-tcf`:

* `-tcf=<path>` - use a TCF file for parsing GCC options.
* `-tcf-debug` - enable printing of debug messages.
* `-tcf-dry-run` - do not execute the final command, only print it.
* `-tcf-help` - show a help message.
* `-tcf-no-compressed` - remove extensions for compressed instructions from `-march` string. It
  removes these extensions: `c`, `zca`, `zcb`, `zcf`, `zcd`, `zcmp`, `zcmt`. It may be useful for targets
  with slow compressed instructions.
* `-tcf-with-memory-defines` - pass memory layout variables from TCF through `-defsym` for a linker file
  for Newlib (takes effect only with `-T arcv.ld`) or Picolibc toolchains (takes effect only with `-specs=picolibc.specs/picolibcpp.specs`). Values for code and data memory layouts are inferred from configurations of ICCM and DCCM
  memory regions in a TCF. If a TCF does not contain CMM, then nothing will be passed to GCC.
* `-tcf-buildlib=<path>` - pass a path to a directory with a buildlib configuration. GCC will use libraries from
  this directory for linking. You can find details in the next section of this README.


An example of using the wrapper with a TCF:

```
$ riscv64-snps-elf-tcf-gcc -g -O2 -tcf=rmx100_dmips.tcf -tcf-debug -specs=picolibc.specs --oslib=semihost --crt0=semihost main.c -o main.elf
...
DEBUG: Running GCC:
<...>/riscv64-snps-elf-gcc -g -O2 -march=rv32i_zicsr_zifencei_zihintpause_a_zca_m_zcb_zcmp_zcmt_zba_zbb_zbs_zicond_zicbom_zicbop -mtune=arc-v-rmx-100-series -mabi=ilp32 -mcmodel=medlow -mno-strict-align --param arcv-mpy-option=1c -specs=picolibc.specs --oslib=semihost --crt0=semihost main.c -o main.elf
```

Pass memory definitions for a linker script:

```
$ riscv64-snps-elf-tcf-gcc -g -O2 -tcf=rmx100_dmips.tcf -tcf-debug -tcf-with-memory-defines -specs=picolibc.specs --oslib=semihost --crt0=semihost main.c -o main.elf
...
DEBUG: Running GCC:
<...>/riscv64-snps-elf-gcc -g -O2 -march=rv32i_zicsr_zifencei_zihintpause_a_zca_m_zcb_zcmp_zcmt_zba_zbb_zbs_zicond_zicbom_zicbop -mtune=arc-v-rmx-100-series -mabi=ilp32 -mcmodel=medlow -mno-strict-align --param arcv-mpy-option=1c -Wl,-defsym=txtmem_addr=0x0 -Wl,-defsym=__flash=0x0 -Wl,-defsym=txtmem_len=0x8000 -Wl,-defsym=__flash_size=0x8000 -Wl,-defsym=datamem_addr=0x80000000 -Wl,-defsym=__ram=0x80000000 -Wl,-defsym=datamem_len=0x8000 -Wl,-defsym=__ram_size=0x8000 -specs=picolibc.specs --oslib=semihost --crt0=semihost main.c -o main.elf
```

## The Buildlib tool

### Overview

The Buildlib tool allows building all toolchain libraries for a particular set
of target and optimization options and then building applications using these prebuilt libraries.
Buildlib builds `libgcc`, Picolibc, and `libstdc++`.

Here is a list of usage examples:

* Build libraries for `rhx100_base.tcf` TCF template:

   ```plain
   $ riscv64-snps-elf-buildlib --output rhx100_base --tcf rhx100_base.tcf --nproc 4
   INFO: Found GCC in PATH: /SCRATCH/ykolerov/tools/gcc-arcv-elf-picolibc-latest/bin/riscv64-snps-elf-gcc
   INFO: Final target options:
   -march=rv32i_zicsr_zifencei_zihintpause_a_zca_m_zcb_zcmp_zba_zbb_zbs_zicond_zicbom_zicbop -mabi=ilp32 -mtune=arc-v-rhx-100-series -mcmodel=medlow
   INFO: Final cflags:
   -mno-strict-align -g -O2
   INFO: Cloning Picolibc repository.
   INFO: Creating a build directory: /home/ykolerov/workspace/arc-v/gcc-buildlib/custom-build/arcv-tcf-wrapper/rhx100_base/build-picolibc
   INFO: Configuring Picolibc library.
   INFO: Building Picolibc library.
   INFO: Installing Picolibc library.
   INFO: Cloning GCC repository.
   INFO: Downloading GCC dependencies.
   INFO: Creating a build directory: /home/ykolerov/workspace/arc-v/gcc-buildlib/custom-build/arcv-tcf-wrapper/rhx100_base/build-gcc
   INFO: Configuring GCC.
   INFO: Building libgcc and libstdc++.
   INFO: Installing libgcc and libstdc++.
   INFO: Saving buildlib.specs.
   INFO: Finished building and installing libgcc and libstdc++.

   $ riscv64-snps-elf-tcf-gcc -tcf=rhx100_base.tcf -tcf-buildlib=./rhx100_base -specs=picolibc.specs --oslib=semihost --crt0=semihost hello.c -o hello.elf
   ```

* Pass all target options explicitly without using a TCF and then build your application with the prebuilt libraries:

   ```
   $ riscv64-snps-elf-buildlib --output buildlib --march rv32imac --mabi ilp32 --mtune arc-v-rmx-100-series --cflags="-g -O3" -j 4
   ...
   $ riscv64-snps-elf-tcf-gcc -march=rv32imac -mabi=ilp32 -mtune=arc-v-rmx-100-series -tcf-buildlib=./buildlib -specs=picolibc.specs --oslib=semihost --crt0=semihost hello.c -o hello.elf
   ```

Here is a list of all command line options:

* `-h, --help` - show the help message and exit.
* `--output PATH, -bd PATH, -buildlib_dir PATH` - set the path to the output directory.
* `--tcf TCF, -tcf TCF` - set the path to a TCF configuration file.
* `--march ARCH, -march ARCH` - set the value for the `-march` target option.
* `--mabi ABI, -mabi ABI` - set the value for the `-mabi` target option.
* `--mtune TUNE, -mtune TUNE` - set the value for the `-mtune` target option.
* `--mcmodel CMODEL, -mcmodel CMODEL` - set the value for the `-mcmodel` target option.
  By default, `-mcmodel=medlow` for `rv32` and `-mcmodel=medany` for `rv64`.
* `--cflags CFLAGS` - pass extra target flags to GCC (default: `-g0 -O2`).
* `--no-libstdcpp, -nocplus` - do not build libstdc++ library.
* `--gcc-sources-git-branch PATH` - set the release branch for GCC (default: `arc-2026.03`).
* `--gcc-sources-dir-path PATH` - set the path to GCC sources (overrides `--gcc-sources-git-branch`).
* `--picolibc-sources-git-branch PATH` - set the release branch for Picolibc (default: `arc-2026.03`).
* `--picolibc-sources-dir-path PATH` - set the path to Picolibc sources (overrides `--picolibc-sources-git-branch`).
* `--flash-addr ADDR` - set the default value for the flash address (default: `0x0`).
* `--flash-size SIZE` - set the default value for the flash size (default: `128K`).
* `--ram-addr ADDR` - set the default value for the RAM address (default: `0x40000000`).
* `--ram-size SIZE` - set the default value for the RAM size (default: `128K`).
* `--nproc N, -j N` - set the number of threads for building (default: 1).
* `--no-clean, -noclean` - do not delete build artifacts.
* `--debug, -v` - show debug messages.

### Known issues

* The `--cflags` option works correctly only in the `--cflags=".."` form.
* The Buildlib tool works only with a Picolibc toolchain for ARC-V.

### Technical details

These steps are performed to build a custom configuration:

* First, buildlib tries to find riscv64-snps-elf-gcc in PATH or in a local directory. It fails if GCC cannot be found.
* Create the main buildlib directory and build directories for Picolibc and GCC. Create symbolic links for Picolibc and GCC sources.
* Configure, build, and install Picolibc and then GCC. All libraries are installed to the buildlib directory.
* Delete symbolic links to sources and build directories for Picolibc and GCC (if `--no-clean` is not passed).

Basically, a buildlib directory is a subset of the toolchain's directory.
Here is a buildlib directory structure:

```
$ tree -d -L 3 buildlib
buildlib
├── lib
│   └── gcc
│       └── riscv64-snps-elf
├── riscv64-snps-elf
│   ├── include
│   │   ├── arpa
│   │   ├── bits
│   │   ├── c++
│   │   ├── machine
│   │   ├── rpc
│   │   ├── ssp
│   │   └── sys
│   ├── lib
│   └── sys-include
│       ├── arpa
│       ├── bits
│       ├── machine
│       ├── rpc
│       ├── ssp
│       └── sys
└── share
    └── gcc-15.2.0
        └── python
```

To build and link an application with a custom library, you need to pass extra arguments:

* `-specs=./buildlib/buildlib.specs` - include a `.specs` file which turns off default multilib rules.
* `-isystem ./buildlib/riscv64-snps-elf/sys-include -isystem ./buildlib/riscv64-snps-elf/include` - use includes from a custom Picolibc build.
* `-B./buildlib/lib/gcc -B./buildlib/riscv64-snps-elf/lib` - use custom libraries by default instead of original ones.

Now consider this example:

```c
int main()
{
    printf("Hello, World!\n");
    return 0;
}
```

How to link an application with custom libraries (also, we pass
`-Wl,-t` to ensure that custom libraries are linked with our application):

```
$ riscv64-snps-elf-gcc \
     -march=rv32imac \
     -mabi=ilp32 \
     -mtune=arc-v-rmx-100-series \
     -mcmodel=medlow \
     -isystem ./buildlib/riscv64-snps-elf/sys-include \
     -isystem ./buildlib/riscv64-snps-elf/include \
     -B./buildlib/lib/gcc \
     -B./buildlib/riscv64-snps-elf/lib \
     -specs=picolibc.specs \
     -specs=buildlib.specs \
     --oslib=semihost \
     --crt0=semihost \
     hello.c -o hello.elf \
    -Wl,-t
./buildlib/riscv64-snps-elf/lib/crt0-semihost.o
/tmp/ccUptbxg.o
./buildlib/lib/gcc/riscv64-snps-elf/15.2.0/libgcc.a
./buildlib/lib/gcc/riscv64-snps-elf/15.2.0/libgcc.a
./buildlib/riscv64-snps-elf/lib/libc.a
./buildlib/riscv64-snps-elf/lib/libsemihost.a
./buildlib/lib/gcc/riscv64-snps-elf/15.2.0/libgcc.a
./buildlib/riscv64-snps-elf/lib/libc.a
./buildlib/riscv64-snps-elf/lib/libsemihost.a
./buildlib/lib/gcc/riscv64-snps-elf/15.2.0/libgcc.a
```

Now we can run the example in nSIM:

```
$ nsimdrv -p nsim_isa_family=rv32 -p nsim_isa_ext=-all.i.m.a.c.zicsr -p nsim_semihosting=1 -p enable_exceptions=0 hello.elf
Hello, World!
```
