import pytest

from arcgnulib import (
    TCF,
    TCFCompilerConfigurationNotFoundError,
    TCFMemoryConfigurationNotFoundError,
    TCFTargetOptionError,
)


TCF_RV32_MINIMAL = """<?xml version="1.0"?>
<configuration>
  <configuration name="gcc_compiler">
    <string>-march=rv32imac -mtune=arc-v-rmx-100-series -mabi=ilp32 -mno-strict-align --param arcv-mpy-option=1c</string>
  </configuration>
  <configuration name="nSIM">
    <string>iccm0_base=0x0 iccm0_size=0x20000 dccm_base=0x200000 dccm_size=0x8000</string>
  </configuration>
</configuration>
"""

TCF_RV32_COMPRESSED = """<?xml version="1.0"?>
<configuration>
  <configuration name="gcc_compiler">
    <string>-march=rv32imafdc_zca_zcb_zcmp_zcmt_zcf_zcd_zicond_zicbom_zicbop_zicsr -mtune=arc-v-rmx-100-series -mabi=ilp32d</string>
  </configuration>
  <configuration name="nSIM">
    <string>iccm0_base=0x0 iccm0_size=0x20000 dccm_base=0x200000 dccm_size=0x8000</string>
  </configuration>
</configuration>
"""

TCF_RV32_MICRO = """<?xml version="1.0"?>
<configuration>
  <configuration name="gcc_compiler">
    <string>-march=rv32e_zifencei_zihintpause_zicbom_zicbop -mabi=ilp32e -mtune=arc-v-rmx-100-series -mstrict-align</string>
  </configuration>
  <configuration name="nSIM">
    <string>iccm0_base=0x0 iccm0_size=0x20000 dccm_base=0x200000 dccm_size=0x8000</string>
  </configuration>
</configuration>
"""

TCF_RV32_USDP = """<?xml version="1.0"?>
<configuration>
  <configuration name="gcc_compiler">
    <string>-march=rv32e_zicsr_zifencei_zihintpause_zca_zcb_zcmp_zcmt_zba_zbb_zbs_zicond_zicbom_zicbop_xarcvudsp -mabi=ilp32e -mtune=arc-v-rmx-100-series -mstrict-align</string>
  </configuration>
  <configuration name="nSIM">
    <string>iccm0_base=0x0 iccm0_size=0x20000 dccm_base=0x200000 dccm_size=0x8000</string>
  </configuration>
</configuration>
"""

TCF_RV64_MINIMAL = """<?xml version="1.0"?>
<configuration>
  <configuration name="gcc_compiler">
    <string>-march=rv64imac -mtune=arc-v-rpx-100-series -mabi=ilp32 -mno-strict-align</string>
  </configuration>
  <configuration name="nSIM">
    <string>iccm0_base=0x0 iccm0_size=0x20000 dccm_base=0x200000 dccm_size=0x8000</string>
  </configuration>
</configuration>
"""

TCF_RV64_FEATURED = """<?xml version="1.0"?>
<configuration>
  <configuration name="gcc_compiler">
    <string>-march=rv64i_zicsr_zifencei_zihintpause_a_zca_zcd_d_f_m_zcb_zba_zbb_zbc_zbs_zicond_zfa_zfh_zicbom_zicbop -mtune=arc-v-rpx-100-series -mabi=lp64d</string>
  </configuration>
  <configuration name="nSIM">
    <string>iccm0_base=0x0 iccm0_size=0x20000 dccm_base=0x200000 dccm_size=0x8000</string>
  </configuration>
</configuration>
"""


class TestTCF:
    def test_rv32_minimal_base(self):
        tcf = TCF(TCF_RV32_MINIMAL)
        assert tcf.get_march(no_compressed=False) == "rv32imac"
        assert tcf.get_march(no_compressed=True) == "rv32i_m_a"
        assert tcf.get_mtune() == "arc-v-rmx-100-series"
        assert tcf.get_mabi() == "ilp32"
        assert tcf.get_mcmodel() == "medlow"

    def test_rv32_minimal_compile_options(self):
        tcf = TCF(TCF_RV32_MINIMAL)
        assert tcf.get_compile_options() == [
            "-march=rv32imac",
            "-mtune=arc-v-rmx-100-series",
            "-mabi=ilp32",
            "-mcmodel=medlow",
            "-mno-strict-align",
            "--param",
            "arcv-mpy-option=1c",
        ]
        assert tcf.get_compile_options(no_compressed=True) == [
            "-march=rv32i_m_a",
            "-mtune=arc-v-rmx-100-series",
            "-mabi=ilp32",
            "-mcmodel=medlow",
            "-mno-strict-align",
            "--param",
            "arcv-mpy-option=1c",
        ]

    def test_rv32_minimal_memory_options(self):
        tcf = TCF(TCF_RV32_MINIMAL)
        assert tcf.get_memory_options() == [
            "-Wl,-defsym=txtmem_addr=0x0",
            "-Wl,-defsym=__flash=0x0",
            "-Wl,-defsym=txtmem_len=0x20000",
            "-Wl,-defsym=__flash_size=0x20000",
            "-Wl,-defsym=datamem_addr=0x200000",
            "-Wl,-defsym=__ram=0x200000",
            "-Wl,-defsym=datamem_len=0x8000",
            "-Wl,-defsym=__ram_size=0x8000",
        ]

    def test_rv32_compressed_base(self):
        tcf = TCF(TCF_RV32_COMPRESSED)
        assert tcf.get_march(no_compressed=False) == "rv32imafdc_zca_zcb_zcmp_zcmt_zcf_zcd_zicond_zicbom_zicbop_zicsr"
        assert tcf.get_march(no_compressed=True) == "rv32i_m_a_f_d_zicond_zicbom_zicbop_zicsr"
        assert tcf.get_mtune() == "arc-v-rmx-100-series"
        assert tcf.get_mabi() == "ilp32d"
        assert tcf.get_mcmodel() == "medlow"

    def test_rv32_micro_base(self):
        tcf = TCF(TCF_RV32_MICRO)
        assert tcf.get_march(no_compressed=False) == "rv32e_zifencei_zihintpause_zicbom_zicbop"
        assert tcf.get_march(no_compressed=True) == "rv32e_zifencei_zihintpause_zicbom_zicbop"
        assert tcf.get_mtune() == "arc-v-rmx-100-series"
        assert tcf.get_mabi() == "ilp32e"
        assert tcf.get_mcmodel() == "medlow"

    def test_rv32_usdp_base(self):
        tcf = TCF(TCF_RV32_USDP)
        assert tcf.get_march(no_compressed=False) == "rv32e_zicsr_zifencei_zihintpause_zca_zcb_zcmp_zcmt_zba_zbb_zbs_zicond_zicbom_zicbop_xarcvudsp"
        assert tcf.get_march(no_compressed=True) == "rv32e_zicsr_zifencei_zihintpause_zba_zbb_zbs_zicond_zicbom_zicbop_xarcvudsp"
        assert tcf.get_mtune() == "arc-v-rmx-100-series"
        assert tcf.get_mabi() == "ilp32e"
        assert tcf.get_mcmodel() == "medlow"

    def test_rv64_minimal_base(self):
        tcf = TCF(TCF_RV64_MINIMAL)
        assert tcf.get_march(no_compressed=False) == "rv64imac"
        assert tcf.get_march(no_compressed=True) == "rv64i_m_a"
        assert tcf.get_mtune() == "arc-v-rpx-100-series"
        assert tcf.get_mabi() == "ilp32"
        assert tcf.get_mcmodel() == "medany"

    def test_rv64_minimal_compile_options(self):
        tcf = TCF(TCF_RV64_MINIMAL)
        assert tcf.get_compile_options() == ["-march=rv64imac", "-mtune=arc-v-rpx-100-series", "-mabi=ilp32", "-mcmodel=medany", "-mno-strict-align"]
        assert tcf.get_compile_options(no_compressed=True) == [
            "-march=rv64i_m_a",
            "-mtune=arc-v-rpx-100-series",
            "-mabi=ilp32",
            "-mcmodel=medany",
            "-mno-strict-align",
        ]

    def test_rv64_minimal_memory_options(self):
        tcf = TCF(TCF_RV64_MINIMAL)
        assert tcf.get_memory_options() == [
            "-Wl,-defsym=txtmem_addr=0x0",
            "-Wl,-defsym=__flash=0x0",
            "-Wl,-defsym=txtmem_len=0x20000",
            "-Wl,-defsym=__flash_size=0x20000",
            "-Wl,-defsym=datamem_addr=0x200000",
            "-Wl,-defsym=__ram=0x200000",
            "-Wl,-defsym=datamem_len=0x8000",
            "-Wl,-defsym=__ram_size=0x8000",
        ]

    def test_rv64_featured_base(self):
        tcf = TCF(TCF_RV64_FEATURED)
        assert (
            tcf.get_march(no_compressed=False) == "rv64i_zicsr_zifencei_zihintpause_a_zca_zcd_d_f_m_zcb_zba_zbb_zbc_zbs_zicond_zfa_zfh_zicbom_zicbop"
        )
        assert tcf.get_march(no_compressed=True) == "rv64i_zicsr_zifencei_zihintpause_a_d_f_m_zba_zbb_zbc_zbs_zicond_zfa_zfh_zicbom_zicbop"
        assert tcf.get_mtune() == "arc-v-rpx-100-series"
        assert tcf.get_mabi() == "lp64d"
        assert tcf.get_mcmodel() == "medany"


class TestTCFExceptions:
    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            TCF.from_file("/nonexistent/path/to/file.tcf")

    def test_compiler_configuration_not_found(self):
        tcf = """<?xml version="1.0"?>
<configuration>
  <configuration name="nSIM">
    <string>iccm0_base=0x0 iccm0_size=0x20000 dccm_base=0x200000 dccm_size=0x8000</string>
  </configuration>
</configuration>
"""
        with pytest.raises(TCFCompilerConfigurationNotFoundError) as _:
            TCF(tcf)

    def test_memory_configuration_not_found(self):
        tcf = """<?xml version="1.0"?>
<configuration>
  <configuration name="gcc_compiler">
    <string>-march=rv32imac -mtune=arc-v-rmx-100-series -mabi=ilp32</string>
  </configuration>
</configuration>
"""
        with pytest.raises(TCFMemoryConfigurationNotFoundError) as _:
            TCF(tcf)

    def test_missing_march(self):
        tcf = """<?xml version="1.0"?>
<configuration>
  <configuration name="gcc_compiler">
    <string>-mtune=arc-v-rmx-100-series -mabi=ilp32</string>
  </configuration>
  <configuration name="nSIM">
    <string>iccm0_base=0x0 iccm0_size=0x20000 dccm_base=0x200000 dccm_size=0x8000</string>
  </configuration>
</configuration>
"""
        with pytest.raises(TCFTargetOptionError) as _:
            TCF(tcf)

    def test_missing_mtune(self):
        tcf = """<?xml version="1.0"?>
<configuration>
  <configuration name="gcc_compiler">
    <string>-march=rv32imac -mabi=ilp32</string>
  </configuration>
  <configuration name="nSIM">
    <string>iccm0_base=0x0 iccm0_size=0x20000 dccm_base=0x200000 dccm_size=0x8000</string>
  </configuration>
</configuration>
"""
        with pytest.raises(TCFTargetOptionError) as _:
            TCF(tcf)

    def test_missing_mabi(self):
        tcf = """<?xml version="1.0"?>
<configuration>
  <configuration name="gcc_compiler">
    <string>-march=rv32imac -mtune=arc-v-rmx-100-series</string>
  </configuration>
  <configuration name="nSIM">
    <string>iccm0_base=0x0 iccm0_size=0x20000 dccm_base=0x200000 dccm_size=0x8000</string>
  </configuration>
</configuration>
"""
        with pytest.raises(TCFTargetOptionError) as _:
            TCF(tcf)

    def test_invalid_march(self):
        tcf = """<?xml version="1.0"?>
<configuration>
  <configuration name="gcc_compiler">
    <string>-march=rv128i -mtune=arc-v-rmx-100-series -mabi=ilp32</string>
  </configuration>
  <configuration name="nSIM">
    <string>iccm0_base=0x0 iccm0_size=0x20000 dccm_base=0x200000 dccm_size=0x8000</string>
  </configuration>
</configuration>
"""
        with pytest.raises(TCFTargetOptionError) as _:
            TCF(tcf)
