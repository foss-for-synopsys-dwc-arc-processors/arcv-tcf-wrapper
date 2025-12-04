# Scripts for GNU Toolchain for ARC-V Targets

This repository contains 2 useful scripts for ARC-V GNU toolchain:

1. `riscv64-snps-elf-tcf-gcc` tool is a TCF wrapper for GCC for ARC-V targets.
   It's intended to be used with TCF files originally prepared for MetaWare tools.
2. `riscv64-snps-elf-buildlib` tool allows building Picolibc, `libgcc` and `libstdc++`
   for a particular set of target and optimization options. Then this configuration
   may be used for building applications using the TCF wrapper.

## Installation

Copy all script to the `bin` directory of a toolchain or add a directory with scripts
to `PATH`. Note that both scripts try to locate `riscv64-snps-elf-gcc` in 2 places:

1. **The same directory where scripts reside.**
   
   If scripts' directory contains `riscv64-snps-elf-gcc`, then this binary is used.
2. **The directory in `PATH`.**

## Usage

### TCF Wrapper

To pass TCF to the wrapper use `-tcf=...` option. Other options are passed
directly to GCC:

```
$ riscv64-snps-elf-tcf-gcc -tcf=rmx100_base.tcf -specs=semihost.specs -specs=arcv.specs -T arcv.ld main.c -o main.elf
riscv64-snps-elf-gcc -march=rv32i_zicsr_zifencei_zihintpause_c_m_zcb_zcmp_zcmt_zba_zbb_zbs_zicond_zicbom_zicbop -mcmodel=medlow -mabi=ilp32 -mtune=arc-v-rmx-100-series -Wl,-defsym=txtmem_addr=0x0 -Wl,-defsym=txtmem_len=0x8000 -Wl,-defsym=datamem_addr=0x80000000 -Wl,-defsym=datamem_len=0x8000 -specs=semihost.specs -specs=arcv.specs -T arcv.ld main.c -o main.elf
```

If `-tcf=...` is omitted, then everything is passed right to GCC without any
extra options:

```
$ riscv64-snps-elf-tcf-gcc -march=rv32i -mabi=ilp32 -specs=semihost.specs -specs=arcv.specs -T arcv.ld main.c -o main.elf
riscv64-snps-elf-gcc -march=rv32i -mabi=ilp32 -specs=semihost.specs -specs=arcv.specs -T arcv.ld main.c -o main.elf
```

Use `-tcf-help` option to print out information about all available wrapper-specific
options.

### Buildlib

Buildlib tool allows building all toolchain libraries for a particular set
of target and optimization options.

Build libraries for `rhx100_base.tcf` template:

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
```

Then you can use these libraries for building applications. You can use the same template for consistency:

```plain
$ riscv64-snps-elf-tcf-gcc -tcf=rhx100_base.tcf -tcf-buildlib=./rhx100_base -specs=picolibc.specs --oslib=semihost --crt0=semihost hello.c -o hello.elf
riscv64-snps-elf-gcc -mno-strict-align -march=rv32i_zicsr_zifencei_zihintpause_a_zca_m_zcb_zcmp_zba_zbb_zbs_zicond_zicbom_zicbop -mabi=ilp32 -mtune=arc-v-rhx-100-series -Wl,-defsym=txtmem_addr=0x0 -Wl,-defsym=__flash=0x0 -Wl,-defsym=txtmem_len=0x20000 -Wl,-defsym=__flash_size=0x20000 -Wl,-defsym=datamem_addr=0x200000 -Wl,-defsym=__ram=0x200000 -Wl,-defsym=datamem_len=0x8000 -Wl,-defsym=__ram_size=0x8000 -specs=/home/ykolerov/workspace/arc-v/gcc-buildlib/custom-build/arcv-tcf-wrapper/rhx100_base/buildlib.specs -B/home/ykolerov/workspace/arc-v/gcc-buildlib/custom-build/arcv-tcf-wrapper/rhx100_base/lib/gcc -B/home/ykolerov/workspace/arc-v/gcc-buildlib/custom-build/arcv-tcf-wrapper/rhx100_base/riscv64-snps-elf/lib -specs=picolibc.specs --oslib=semihost --crt0=semihost hello.c -o hello.elf

$ nsimdrv -tcf rhx100_base.tcf -p nsim_semihosting=1 -p enable_exceptions=0 hello.elf
Hello, World!
```

Use `--help` option to print out information about all available wrapper-specific
options.
