# TCF Wrapper for GNU Toolchain for ARC-V Targets

`riscv64-snps-elf-tcf-gcc` tool is a TCF wrapper for GCC for ARC-V targets.
It's intended to be used with TCF files originally prepared for MetaWare tools.

## Installation

The wrapper is tries to find `riscv64-snps-elf-gcc` in 2 places:

1. **Put the script to the directory with `riscv64-snps-elf-gcc` binary.**
   
   If script's directory contains `riscv64-snps-elf-gcc`, then this binary is used.
2. **Or ensure that `riscv64-snps-elf-gcc` is in your `PATH`.**

## Usage

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
