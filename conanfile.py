import os
import pathlib
from conan import ConanFile
from conan.tools import files
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout


class CAFConan(ConanFile):
    name = "caf"
    version = "0.17.4-lmx.15"
    description = "An open source implementation of the Actor Model in C++"
    url = "https://github.com/bincrafters/conan-caf"
    homepage = "https://github.com/actor-framework/actor-framework"
    topics = ("conan", "caf", "actor-framework", "actor-model", "pattern-matching", "actors")
    license = ("BSD-3-Clause, BSL-1.0")
    exports = ["LICENSE"]
    exports_sources = ["CMakeLists.txt", "cmake/*", "doc/*", "libcaf*"]
    generators = "CMakeDeps"
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "log_level": ["ERROR", "WARNING", "INFO", "DEBUG", "TRACE", "QUIET"],
        "openssl": [True, False],
        "io_module": [True, False],
        "always_allow_unsafe": [True, False],
    }
    default_options = {"shared": False, "fPIC": True, "log_level": "QUIET", "openssl": False,
                       "io_module": False, "always_allow_unsafe": True}
    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    @property
    def _is_static(self):
        return 'shared' not in self.options or not self.options.shared

    @property
    def _has_openssl(self):
        return 'openssl' in self.options and self.options.openssl

    def layout(self):
        cmake_layout(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
            del self.options.shared
            if self.settings.arch == "x86":
                del self.options.openssl

    def requirements(self):
        if self._has_openssl:
            self.requires("openssl/1.0.2u")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CAF_NO_AUTO_LIBCPP"] = True
        tc.variables["CAF_NO_OPENSSL"] = not self._has_openssl
        for define in ["CAF_NO_EXAMPLES", "CAF_NO_TOOLS", "CAF_NO_UNIT_TESTS", "CAF_NO_PYTHON", "CAF_NO_OPENCL"]:
            tc.variables[define] = "ON"
        if self.settings.os == "Macos" and self.settings.arch == "x86":
            tc.variables["CMAKE_OSX_ARCHITECTURES"] = "i386"
        tc.variables["CAF_BUILD_STATIC"] = self._is_static
        tc.variables["CAF_BUILD_STATIC_ONLY"] = self._is_static
        tc.variables["CAF_LOG_LEVEL"] = self.options.log_level
        if self.settings.os == 'Windows':
            tc.variables["OPENSSL_USE_STATIC_LIBS"] = True
            tc.variables["OPENSSL_MSVC_STATIC_RT"] = True
        elif self.settings.compiler == 'clang':
            tc.variables["PTHREAD_LIBRARIES"] = "-pthread -ldl"
        else:
            tc.variables["PTHREAD_LIBRARIES"] = "-pthread"
        tc.variables["CAF_NO_IO"] = not self.options.io_module
        tc.variables["CAF_ALWAYS_ALLOW_UNSAFE"] = self.options.always_allow_unsafe
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        pck_folder = pathlib.Path(self.package_folder)
        files.copy(self, pattern="LICENSE*", src=self.source_folder, dst=pck_folder / "licenses")
        cmake = CMake(self)
        cmake.configure()
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = files.collect_libs(self)
        if self.settings.os == "Windows":
            self.cpp_info.system_libs.extend(["ws2_32", "iphlpapi", "psapi"])
        elif self.settings.os == "Linux":
            self.cpp_info.system_libs.extend(['-pthread', 'm'])
