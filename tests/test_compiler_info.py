import os
from pathlib import Path

import pytest

import arcgnulib
from arcgnulib import CompilerInfo

COMPILER_FILENAME = "riscv64-snps-elf-gcc"
COMPILER_FILENAME_ALIAS = "riscv64-elf-gcc"
MOCK_COMPILERS_DIR = Path(__file__).resolve().parent / "mock_compilers"


class TestCompilerInfo:
    def test_compiler_info_gcc_not_found(self):
        with pytest.raises(arcgnulib.CompilerInfoGCCNotFoundError):
            CompilerInfo("gcc-not-found")

    def test_compiler_info_gcc_execution_error(self):
        with pytest.raises(arcgnulib.CompilerInfoGCCExecutionError):
            CompilerInfo("date")

    def test_compiler_info_gcc_compiler_name(self, monkeypatch):
        monkeypatch.setenv("PATH", str(MOCK_COMPILERS_DIR), prepend=os.pathsep)
        compiler_info = CompilerInfo(COMPILER_FILENAME)
        assert compiler_info.get_compiler_name() == COMPILER_FILENAME

    def test_compiler_info_gcc_compiler_triplet(self, monkeypatch):
        monkeypatch.setenv("PATH", str(MOCK_COMPILERS_DIR), prepend=os.pathsep)
        compiler_info = CompilerInfo(COMPILER_FILENAME)
        assert compiler_info.get_compiler_triplet() == "riscv64-snps-elf"

    def test_compiler_info_gcc_compiler_triplet_alias(self, monkeypatch):
        monkeypatch.setenv("PATH", str(MOCK_COMPILERS_DIR), prepend=os.pathsep)
        compiler_info = CompilerInfo(COMPILER_FILENAME_ALIAS)
        assert compiler_info.get_compiler_triplet() == "riscv64-snps-elf"
