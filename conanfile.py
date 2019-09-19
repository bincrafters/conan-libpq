#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, AutoToolsBuildEnvironment, tools
from conans.errors import ConanInvalidConfiguration
import os


class LibpqConan(ConanFile):
    name = "libpq"
    version = "11.3"
    description = "The library used by all the standard PostgreSQL tools."
    topics = ("conan", "libpq", "postgresql", "database", "db")
    url = "https://github.com/bincrafters/conan-libpq"
    homepage = "https://www.postgresql.org/docs/current/static/libpq.html"
    author = "Bincrafters <bincrafters@gmail.com>"
    license = "PostgreSQL"
    exports = ["LICENSE.md"]
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_zlib": [True, False],
        "with_openssl": [True, False],
        "disable_rpath": [True, False]}
    default_options = {'shared': False, 'fPIC': True, 'with_zlib': False, 'with_openssl': False, 'disable_rpath': False}
    _source_subfolder = "source_subfolder"
    _build_subfolder = None
    _autotools = None

    def config_options(self):
        if self.settings.os == 'Windows':
            del self.options.fPIC
            del self.options.shared

    def configure(self):
        if self.settings.os == "Windows" and self.settings.compiler == "Visual Studio":
            raise ConanInvalidConfiguration("Visual Studio is not supported yet.")
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd

    def requirements(self):
        if self.options.with_zlib:
            self.requires.add("zlib/1.2.11@conan/stable")
        if self.options.with_openssl:
            self.requires.add("OpenSSL/1.0.2r@conan/stable")

    def source(self):
        source_url = "https://ftp.postgresql.org/pub/source"
        sha256 = "2a9ff3659e327a4369929478200046942710fd6bc25fe56c72d6b01ee8b1974a"
        tools.get("{0}/v{1}/postgresql-{2}.tar.gz".format(source_url, self.version, self.version), sha256=sha256)
        extracted_dir = "postgresql-" + self.version
        os.rename(extracted_dir, self._source_subfolder)

    def _configure_autotools(self):
        if not self._autotools:
            self._autotools = AutoToolsBuildEnvironment(self, win_bash=tools.os_info.is_windows)
            self._build_subfolder = os.path.join(self.build_folder, "output")
            args = ['--without-readline']
            args.append('--with-zlib' if self.options.with_zlib else '--without-zlib')
            args.append('--with-openssl' if self.options.with_openssl else '--without-openssl')
            if self.options.disable_rpath:
                args.append('--disable-rpath')
            with tools.chdir(self._source_subfolder):
                self._autotools.configure(args=args)
        return self._autotools

    def build(self):
        autotools = self._configure_autotools()
        with tools.chdir(os.path.join(self._source_subfolder, "src", "common")):
            autotools.make()
        with tools.chdir(os.path.join(self._source_subfolder, "src", "interfaces", "libpq")):
            autotools.make()

    def package(self):
        self.copy(pattern="COPYRIGHT", dst="licenses", src=self._source_subfolder)
        autotools = self._configure_autotools()
        with tools.chdir(os.path.join(self._source_subfolder, "src", "common")):
            autotools.install()
        with tools.chdir(os.path.join(self._source_subfolder, "src", "interfaces", "libpq")):
            autotools.install()
        self.copy(pattern="*.h", dst="include", src=os.path.join(self._build_subfolder, "include"))
        self.copy(pattern="*.h", dst=os.path.join("include", "catalog"), src=os.path.join(self._source_subfolder, "src", "include", "catalog"))
        self.copy(pattern="*.h", dst=os.path.join("include", "catalog"), src=os.path.join(self._source_subfolder, "src", "backend", "catalog"))
        self.copy(pattern="postgres_ext.h", dst="include", src=os.path.join(self._source_subfolder, "src", "include"))
        self.copy(pattern="pg_config_ext.h", dst="include", src=os.path.join(self._source_subfolder, "src", "include"))
        if self.settings.os == "Linux":
            pattern = "*.so*" if self.options.shared else "*.a"
        elif self.settings.os == "Macos":
            pattern = "*.dylib" if self.options.shared else "*.a"
        elif self.settings.os == "Windows":
            pattern = "*.a"
            self.copy(pattern="*.dll", dst="bin", src=os.path.join(self._build_subfolder, "bin"))
        self.copy(pattern=pattern, dst="lib", src=os.path.join(self._build_subfolder, "lib"))

    def package_info(self):
        self.env_info.PostgreSQL_ROOT = self.package_folder
        self.cpp_info.libs = tools.collect_libs(self)
        if self.settings.os == "Linux":
            self.cpp_info.libs.append("pthread")
        elif self.settings.os == "Windows":
            self.cpp_info.libs.append("ws2_32")
