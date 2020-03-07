import os
from conans import ConanFile, CMake, tools
from conans.errors import ConanInvalidConfiguration
from conans.tools import Version


class CAFConan(ConanFile):
    name = "caf"
    version = "0.17.3"
    description = "An open source implementation of the Actor Model in C++"
    url = "https://github.com/bincrafters/conan-caf"
    homepage = "https://github.com/actor-framework/actor-framework"
    topics = ("conan", "caf", "actor-framework", "actor-model", "pattern-matching", "actors")
    license = ("BSD-3-Clause, BSL-1.0")
    exports = ["LICENSE.md"]
    exports_sources = ["CMakeLists.txt", "caf.patch"]
    generators = ["cmake"]
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "log_level": ["ERROR", "WARNING", "INFO", "DEBUG", "TRACE", "NONE"],
        "openssl": [True, False]
    }
    default_options = {"shared": False, "fPIC": True, "log_level": "NONE", "openssl": True}
    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    @property
    def _is_static(self):
        return 'shared' not in self.options.values.keys() or not self.options.shared

    @property
    def _has_openssl(self):
        return 'openssl' in self.options.values.keys() and self.options.openssl

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
            del self.options.shared
            if self.settings.arch == "x86":
                del self.options.openssl

    def source(self):
        sha256 = "af235dbb5001a86d716c19f1b597be81bbcf172b87d42e2a38dc3ac97ea3863d"
        tools.get("{}/archive/{}.tar.gz".format(self.homepage, self.version), sha256=sha256)
        os.rename("actor-framework-" + self.version, self._source_subfolder)

    def requirements(self):
        if self._has_openssl:
            self.requires("openssl/1.0.2u")

    def configure(self):
        if self.settings.compiler == "gcc":
            if Version(self.settings.compiler.version.value) < "4.8":
                raise ConanInvalidConfiguration("g++ >= 4.8 is required, yours is %s" % self.settings.compiler.version)
        elif self.settings.compiler == "clang" and Version(self.settings.compiler.version.value) < "4.0":
            raise ConanInvalidConfiguration("clang >= 4.0 is required, yours is %s" % self.settings.compiler.version)
        elif self.settings.compiler == "apple-clang" and Version(self.settings.compiler.version.value) < "9.0":
            raise ConanInvalidConfiguration("clang >= 9.0 is required, yours is %s" % self.settings.compiler.version)
        elif self.settings.compiler == "apple-clang" and Version(self.settings.compiler.version.value) > "10.0" and \
                self.settings.arch == 'x86':
            raise ConanInvalidConfiguration("clang >= 11.0 does not support x86")
        elif self.settings.compiler == "Visual Studio" and Version(self.settings.compiler.version.value) < "15":
            raise ConanInvalidConfiguration("Visual Studio >= 15 is required, yours is %s" % self.settings.compiler.version)

    def _cmake_configure(self):
        cmake = CMake(self)
        cmake.definitions["CMAKE_CXX_STANDARD"] = "11"
        cmake.definitions["CAF_NO_AUTO_LIBCPP"] = True
        cmake.definitions["CAF_NO_OPENSSL"] = not self._has_openssl
        for define in ["CAF_NO_EXAMPLES", "CAF_NO_TOOLS", "CAF_NO_UNIT_TESTS", "CAF_NO_PYTHON"]:
            cmake.definitions[define] = "ON"
        if tools.os_info.is_macos and self.settings.arch == "x86":
            cmake.definitions["CMAKE_OSX_ARCHITECTURES"] = "i386"
        cmake.definitions["CAF_BUILD_STATIC"] = self._is_static
        cmake.definitions["CAF_BUILD_STATIC_ONLY"] = self._is_static
        cmake.definitions["CAF_LOG_LEVEL"] = self.default_options['log_level'].index(self.options.log_level.value)
        if self.settings.os == 'Windows':
            cmake.definitions["OPENSSL_USE_STATIC_LIBS"] = True
            cmake.definitions["OPENSSL_MSVC_STATIC_RT"] = True
        elif self.settings.compiler == 'clang':
            cmake.definitions["PTHREAD_LIBRARIES"] = "-pthread -ldl"
        else:
            cmake.definitions["PTHREAD_LIBRARIES"] = "-pthread"
            if self.settings.compiler == "gcc" and Version(self.settings.compiler.version.value) < "5.0":
                cmake.definitions["CMAKE_SHARED_LINKER_FLAGS"] = "-pthread"
        cmake.configure(build_folder=self._build_subfolder)
        return cmake

    def build(self):
        if self.settings.os == "Windows":  # Needed for MSVC and Mingw
            tools.patch(base_path=self._source_subfolder, patch_file="caf.patch")
        cmake = self._cmake_configure()
        cmake.build()

    def package(self):
        self.copy("LICENSE*", dst="licenses", src=self._source_subfolder)
        cmake = self._cmake_configure()
        cmake.install()

    def package_info(self):
        suffix = "_static" if self._is_static else ""
        self.cpp_info.libs = ["caf_io%s" % suffix, "caf_core%s" % suffix]
        if self._has_openssl:
            self.cpp_info.libs.append("caf_openssl%s" % suffix)
        if self.settings.os == "Windows":
            self.cpp_info.libs.extend(["ws2_32", "iphlpapi", "psapi"])
        elif self.settings.os == "Linux":
            self.cpp_info.libs.extend(['-pthread', 'm'])
