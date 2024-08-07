import subprocess
import sys

from setuptools import setup
from setuptools.command.build_py import build_py


class Build(build_py):
    """Customized setuptools build command - builds protos on build."""
    def run(self):
        protoc_command = ["make", "gen_grpc"]
        if subprocess.call(protoc_command) != 0:
            sys.exit(-1)
        super().run()


setup(
    cmdclass={'build_py': Build}
)
