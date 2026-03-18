import runpy
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

WRAPPER_PATH = Path(__file__).resolve().parent.parent / "riscv64-snps-elf-tcf-gcc"

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


class TestTCFWrapper:
    @pytest.mark.parametrize(
        "args_before_tcf,extra_tcf_flags,args_after_tcf,expected",
        [
            (
                [],
                [],
                [],
                "/mock/riscv64-snps-elf-gcc -march=rv64imac -mtune=arc-v-rpx-100-series " "-mabi=ilp32 -mcmodel=medany -mno-strict-align -c foo.c",
            ),
            (
                [],
                ["-tcf-no-compressed"],
                [],
                "/mock/riscv64-snps-elf-gcc -march=rv64i_m_a -mtune=arc-v-rpx-100-series " "-mabi=ilp32 -mcmodel=medany -mno-strict-align -c foo.c",
            ),
            (
                [],
                ["-tcf-with-memory-defines"],
                [],
                "/mock/riscv64-snps-elf-gcc -march=rv64imac -mtune=arc-v-rpx-100-series "
                "-mabi=ilp32 -mcmodel=medany -mno-strict-align "
                "-Wl,-defsym=txtmem_addr=0x0 -Wl,-defsym=__flash=0x0 "
                "-Wl,-defsym=txtmem_len=0x20000 -Wl,-defsym=__flash_size=0x20000 "
                "-Wl,-defsym=datamem_addr=0x200000 -Wl,-defsym=__ram=0x200000 "
                "-Wl,-defsym=datamem_len=0x8000 -Wl,-defsym=__ram_size=0x8000 -c foo.c",
            ),
            (
                ["-v", "-Wall"],
                ["-tcf-with-memory-defines"],
                ["-O2", "-I/usr/include"],
                "/mock/riscv64-snps-elf-gcc -v -Wall -march=rv64imac -mtune=arc-v-rpx-100-series "
                "-mabi=ilp32 -mcmodel=medany -mno-strict-align "
                "-Wl,-defsym=txtmem_addr=0x0 -Wl,-defsym=__flash=0x0 "
                "-Wl,-defsym=txtmem_len=0x20000 -Wl,-defsym=__flash_size=0x20000 "
                "-Wl,-defsym=datamem_addr=0x200000 -Wl,-defsym=__ram=0x200000 "
                "-Wl,-defsym=datamem_len=0x8000 -Wl,-defsym=__ram_size=0x8000 "
                "-O2 -I/usr/include -c foo.c",
            ),
        ],
    )
    def test_arguments(self, capsys, args_before_tcf, extra_tcf_flags, args_after_tcf, expected):
        """Check that -tcf-dry-run prints the correct GCC command line with TCF options."""
        mock_compiler_info = MagicMock()
        mock_compiler_info.get_compiler_path.return_value = "/mock/riscv64-snps-elf-gcc"
        mock_compiler_info.get_compiler_triplet.return_value = "riscv64-snps-elf"

        with tempfile.TemporaryDirectory() as tmpdir:
            tcf_path = Path(tmpdir) / "test.tcf"
            tcf_path.write_text(TCF_RV64_MINIMAL)

            with patch("arcgnulib.CompilerInfo", return_value=mock_compiler_info):
                old_argv = sys.argv
                try:
                    sys.argv = [
                        "riscv64-snps-elf-tcf-gcc",
                        *args_before_tcf,
                        "-tcf=" + str(tcf_path),
                        "-tcf-dry-run",
                        *extra_tcf_flags,
                        *args_after_tcf,
                        "-c",
                        "foo.c",
                    ]
                    with pytest.raises(SystemExit) as exc_info:
                        runpy.run_path(str(WRAPPER_PATH), run_name="__main__")
                    assert exc_info.value.code == 0
                finally:
                    sys.argv = old_argv

            captured = capsys.readouterr()
            output = captured.out.strip()

        assert output == expected
