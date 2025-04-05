import subprocess

def test_smoke_app_starts():
    proc = subprocess.run(
        ["python", "-m", "typetrace.backend.cli"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=5,
    )
    print("STDOUT:", proc.stdout.decode())
    print("STDERR:", proc.stderr.decode())
    assert proc.returncode == 0, f"TypeTrace failed with return code {proc.returncode}"
