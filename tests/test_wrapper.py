import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


WRAPPER = Path(__file__).resolve().parents[1] / "opencode-sandbox"


class WrapperTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="opencode-sandbox-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project = self.root / "project with spaces"
        self.project.mkdir()
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.host_config = self.root / "config" / "opencode"
        self.host_config.mkdir(parents=True)
        self.env = dict(os.environ, HOME=str(self.root / "home"),
                        XDG_CONFIG_HOME=str(self.root / "config"),
                        XDG_DATA_HOME=str(self.root / "data"),
                        PATH=f"{self.bin}:/usr/bin:/bin", SSH_AUTH_SOCK="",
                        TEST_VERSION="opencode v2.0.7")
        self.write_command("bwrap", """#!/usr/bin/python3
import json, sys
print(json.dumps(sys.argv[1:]))
""")
        self.write_command("opencode", """#!/bin/sh
[ "$#" -eq 1 ] && [ "$1" = --version ] || exit 1
printf '%s\n' "$TEST_VERSION"
""")

    def write_command(self, name, content):
        path = self.bin / name
        path.write_text(content)
        path.chmod(0o755)

    def launch(self, *args):
        result = subprocess.run([str(WRAPPER), *args], cwd=self.project,
                                env=self.env, capture_output=True, text=True,
                                check=True, timeout=10)
        mounts = json.loads(result.stdout)
        executable = str(self.bin / "opencode")
        return mounts, mounts[mounts.index(executable) + 1:]

    def test_v2_private_server_and_argument_boundaries(self):
        for args, expected in [
            ([], ['--standalone']),
            (['.'], ['--standalone', '.']),
            (['run', 'a prompt with spaces'],
             ['run', '--standalone', 'a prompt with spaces']),
            (['mini'], ['mini', '--standalone']),
            (['api', 'get', '/api/info'],
             ['api', '--standalone', 'get', '/api/info']),
            (['session', 'list'], ['session', 'list', '--standalone']),
            (['auth', 'list'], ['auth', 'list', '--standalone']),
            (['--log-level', 'debug', 'models'],
             ['--log-level', 'debug', 'models', '--standalone']),
            (['--print-logs=false', 'run', 'hello'],
             ['--print-logs=false', 'run', '--standalone', 'hello']),
            (['--print-logs=true', 'run', 'hello'],
             ['--print-logs=true', 'run', '--standalone', 'hello']),
            (['session', '--print-logs', 'list'],
             ['session', '--print-logs', 'list', '--standalone']),
            (['auth', '--log-level', 'debug', 'list'],
             ['auth', '--log-level', 'debug', 'list', '--standalone']),
            (['--log-level=debug', 'session', '--print-logs=false', 'list'],
             ['--log-level=debug', 'session', '--print-logs=false', 'list', '--standalone']),
            (['run', '--', '--server'],
             ['run', '--standalone', '--', '--server']),
        ]:
            with self.subTest(args=args):
                self.assertEqual(self.launch(*args)[1], expected)

    def test_explicit_connections_metadata_and_unsupported_commands(self):
        for args in [
            ['--version'], ['--help'], ['run', '--help'],
            ['--completions', 'bash'], ['run', '--standalone', 'hello'],
            ['--server', 'http://localhost:4096'],
            ['api', '--server=http://localhost:4096', 'get', '/api/info'],
            ['serve'], ['service', 'status'], ['auth'], ['session'],
            ['mcp', 'list'], ['plugin', 'list'], ['debug', 'paths'],
        ]:
            with self.subTest(args=args):
                self.assertEqual(self.launch(*args)[1], args)

    def test_v1_and_unknown_versions_pass_arguments_through(self):
        for version in ['1.2.0', 'opencode v1.2.0', 'dev']:
            self.env['TEST_VERSION'] = version
            for args in [[], ['.'], ['run', 'a prompt with spaces'], ['models']]:
                with self.subTest(version=version, args=args):
                    self.assertEqual(self.launch(*args)[1], args)

    def test_v2_version_formats(self):
        for version in ['2.0.7', 'v2.0.7', 'opencode v2.0.7']:
            self.env['TEST_VERSION'] = version
            with self.subTest(version=version):
                self.assertEqual(self.launch('run', 'hello')[1],
                                 ['run', '--standalone', 'hello'])

    def test_failed_version_probe_passes_arguments_through(self):
        self.write_command('opencode', '#!/bin/sh\nexit 1\n')
        self.assertEqual(self.launch('run', 'hello')[1], ['run', 'hello'])

    def test_host_config_is_mounted_read_only_without_copying(self):
        (self.host_config / 'cli.json').write_text('{"theme":"host"}')
        (self.host_config / 'opencode.json').write_text('{}')
        local = self.project / '.sandbox' / 'config' / 'opencode'
        local.mkdir(parents=True)  # Layout left by the old read-only mount.
        (local / 'opencode.json').write_text('{"model":"local"}')
        mounts, _ = self.launch('--version')
        source_index = mounts.index(str(self.host_config))
        self.assertEqual(mounts[source_index - 1], '--ro-bind')
        self.assertEqual(mounts[source_index + 1], str(local))
        self.assertEqual((local / 'opencode.json').read_text(), '{"model":"local"}')
        self.assertFalse((local / 'cli.json').exists())
        self.assertFalse((local.parent / '.opencode-seeded').exists())
        self.assertEqual((self.host_config / 'cli.json').read_text(), '{"theme":"host"}')


if __name__ == '__main__':
    unittest.main()
