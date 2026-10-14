#!/usr/bin/env python3
"""Verify the sample in an isolated Godot project using an existing licensed runtime."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--godot", type=Path, required=True)
    parser.add_argument("--runtime-bin", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    source = Path(__file__).resolve().parents[2]
    if args.evidence.exists():
        parser.error("Evidence directory exists; select a new version")
    platform = {"darwin":"macos", "linux":"linux", "win32":"windows"}.get(sys.platform)
    runtime = args.runtime_bin.resolve()
    if not platform or not (runtime/platform).is_dir() or not (runtime/"spine_godot_extension.gdextension").is_file():
        parser.error("Provide an existing spine-godot bin directory for this platform")
    args.evidence.mkdir(parents=True)
    fingerprints = {str(p.relative_to(source)):digest(p) for p in [
        source/"assets/godot/stationary_turret.gd", source/"tests/godot/test_turret.gd",
        source/"scripts/build_turret.py", source/"scripts/turret_preview.py",
        source/"examples/toywatch-turret/export/toy-turret.spine-json",
        source/"examples/toywatch-turret/export/toy-turret.atlas",
        source/"examples/toywatch-turret/export/toy-turret.png"]}
    runtime_hashes = {str(p.relative_to(runtime)):digest(p) for p in (runtime/platform).rglob("*") if p.is_file()}
    report = {"result":"FAIL", "source_sha256":fingerprints, "runtime_sha256":runtime_hashes}
    with tempfile.TemporaryDirectory(prefix="codex-turret-godot-") as folder:
        project = Path(folder)
        (project/"bin").mkdir()
        shutil.copyfile(runtime/"spine_godot_extension.gdextension",project/"bin/spine_godot_extension.gdextension")
        shutil.copytree(runtime/platform,project/"bin"/platform)
        shutil.copytree(source/"examples/toywatch-turret/export",project/"turret")
        shutil.copyfile(source/"assets/godot/stationary_turret.gd",project/"stationary_turret.gd")
        shutil.copyfile(source/"tests/godot/test_turret.gd",project/"test_turret.gd")
        (project/"project.godot").write_text('config_version=5\n[application]\nconfig/name="Codex turret runtime validation"\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n')
        # Let editor frames drain importer work before closing. On this target
        # engine an immediate cold --import shutdown can crash after importing.
        commands = [("import", ["--editor","--quit-after","120"]), ("runtime",["--script","res://test_turret.gd","--quit-after","120"])]
        for label, extra in commands:
            cmd = [str(args.godot.resolve()),"--headless","--path",str(project),*extra]
            try:
                process = subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=60)
                output, code = process.stdout, process.returncode
            except subprocess.TimeoutExpired as exc:
                output,code = str(exc),124
            (args.evidence/(label+".log")).write_text(output,encoding="utf-8")
            report[label+"_exit_code"] = code
            if code or "SCRIPT ERROR:" in output or "ERROR:" in output:
                print(output)
                break
            if label == "runtime":
                for line in output.splitlines():
                    try:
                        status = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(status,dict) and status.get("result") == "PASS" and status.get("failures") == 0:
                        report.update(status)
                        break
                print(output)
    (args.evidence/"report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    if report["result"] != "PASS":
        parser.exit(1,"Godot verification failed; inspect the saved evidence\n")
    print("Saved runtime evidence:",args.evidence)


if __name__ == "__main__":
    run()
