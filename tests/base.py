import distutils
import importlib
import inspect
import os.path
import requests
import shutil
import subprocess
import sys
import time
import types

try:
    import unittest2 as unittest
except ImportError:
    import unittest


class PyangBindTestCase(unittest.TestCase):
    yang_files = None
    pyang_flags = None
    split_class_dir = False
    module_name = "bindings"
    remote_yang_files = None
    _pyang_generated_class_dir = None

    @classmethod
    def _fetch_remote_yang_files(cls):
        # The structure of cls.remote_yang_files is expected to be as follows:
        #   [ {'local_path': str, 'remote_prefix': str, 'files': [str, ...]}, ...]
        for file_group in cls.remote_yang_files:
            local_path = os.path.join(cls._test_path, file_group["local_path"])
            if not os.path.exists(local_path):
                os.makedirs(local_path)
            for file_path in file_group["files"]:
                file_name = file_path.split("/")[-1]
                local_file_path = os.path.join(local_path, file_name)
                if not os.path.exists(local_file_path):
                    remote_file_path = "%s%s" % (file_group["remote_prefix"], file_path)
                    downloaded = False
                    for i in range(0, 4):
                        response = requests.get(remote_file_path)
                        if response.status_code != 200:
                            time.sleep(2)
                        else:
                            downloaded = True
                            with open(local_file_path, "wb") as fhandle:
                                fhandle.write(response.content)
                            break
                    if not downloaded:
                        raise RuntimeError(
                            "Could not download file: %s (response: %s)" % (remote_file_path, response.status_code)
                        )

    @classmethod
    def setUpClass(cls):
        cls._test_path = os.path.dirname(inspect.getfile(cls))

        if cls.remote_yang_files is not None:
            cls._fetch_remote_yang_files()

        if cls.yang_files is None:
            raise ValueError("cls.yang_files must be set")
        pyang_path = distutils.spawn.find_executable("pyang")
        if not pyang_path:
            raise RuntimeError("Could not locate `pyang` executable.")
        base_dir = os.path.dirname(os.path.dirname(__file__))
        yang_files = [os.path.join(cls._test_path, filename) for filename in cls.yang_files]
        plugin_dir = os.path.join(base_dir, "pyangbind", "plugin")

        flags = cls.pyang_flags or []
        if cls.split_class_dir is True:
            cls._pyang_generated_class_dir = os.path.join(cls._test_path, cls.module_name)
            flags.append("--split-class-dir {}".format(cls._pyang_generated_class_dir))

        pyang_cmd = "{pyang} --plugindir {plugins} -f pybind -p {test_path} {flags} {yang_files}".format(
            pyang=pyang_path,
            plugins=plugin_dir,
            test_path=cls._test_path,
            flags=" ".join(flags),
            yang_files=" ".join(yang_files),
        )
        bindings_code = subprocess.check_output(
            pyang_cmd, shell=True, stderr=subprocess.STDOUT, env={"PYTHONPATH": base_dir}
        )
        if not cls.split_class_dir:
            module = types.ModuleType(cls.module_name)
            exec(bindings_code, module.__dict__)
        else:
            sys.path.append(cls._test_path)
            module = importlib.import_module(cls.module_name)
            sys.path.remove(cls._test_path)
        setattr(cls, cls.module_name, module)

    @classmethod
    def tearDownClass(cls):
        delattr(cls, cls.module_name)
        if cls.split_class_dir:
            del sys.modules[cls.module_name]
            # Remove auto-generated submodules from our system cache
            for module in list(sys.modules.keys()):
                if module.startswith("%s." % cls.module_name):
                    del sys.modules[module]
            shutil.rmtree(cls._pyang_generated_class_dir)
            del cls._pyang_generated_class_dir
        if cls.remote_yang_files:
            yang_paths = set([x["local_path"] for x in cls.remote_yang_files])
            for yang_path in yang_paths:
                shutil.rmtree(os.path.join(cls._test_path, yang_path))
