"""Run the whole Lab 12 pipeline on a Kaggle kernel (GPU T4 machine, internet on).

The lab code is plain numpy (no torch, no CUDA), so the T4 is attached but the work runs on the kernel's CPUs.
Push with:   kaggle kernels push -p kaggle
Fetch with:  kaggle kernels output <user>/k4-track4-day12-lab12 -p <dir>
Outputs:     run_all.log, tests.log, env.txt and lab12_outputs.tar.gz (evidence/ + work/models/)
"""
import os
import shutil
import subprocess
import sys

REPO = "https://github.com/huybla166/K4-Track4-DAY12-PhamQuangHuy-2A202602900.git"
COMMIT = "4e575dfb13716b57d86e579cf66d49665c87880e"     # code with the 10 functions implemented
MSSV = "2A202602900"
SEEDS = 5
OUT = "/kaggle/working"
LAB = "/kaggle/tmp/lab"                                 # outside /kaggle/working so the 195 MB csv is not saved as output
ENV = {**os.environ, "PYTHONUTF8": "1", "PYTHONUNBUFFERED": "1"}


def run(cmd, log=None, cwd=None, check=True):
    """Run a command, stream its output to the kernel log and (optionally) to a file."""
    print("$", " ".join(cmd), flush=True)
    p = subprocess.Popen(cmd, cwd=cwd, env=ENV, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    f = open(log, "w") if log else None
    for line in p.stdout:
        sys.stdout.write(line)
        if f:
            f.write(line)
    p.wait()
    if f:
        f.close()
    if check and p.returncode != 0:
        sys.exit(f"command failed ({p.returncode}): {' '.join(cmd)}")
    return p.returncode


def main():
    with open(f"{OUT}/env.txt", "w") as f:
        f.write(subprocess.run(["nvidia-smi"], capture_output=True, text=True).stdout or "nvidia-smi not available\n")
        f.write(subprocess.run([sys.executable, "-c", "import numpy, pandas, matplotlib, os; print('python', __import__('sys').version);"
                                "print('numpy', numpy.__version__, 'pandas', pandas.__version__, 'matplotlib', matplotlib.__version__);"
                                "print('cpus', os.cpu_count())"], capture_output=True, text=True).stdout)
    print(open(f"{OUT}/env.txt").read(), flush=True)

    shutil.rmtree(LAB, ignore_errors=True)
    os.makedirs(os.path.dirname(LAB), exist_ok=True)
    run(["git", "clone", "-q", REPO, LAB])
    run(["git", "checkout", "-q", COMMIT], cwd=LAB)
    run(["git", "log", "--oneline", "-1"], cwd=LAB)

    run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], log=f"{OUT}/tests.log", cwd=LAB)
    run([sys.executable, "run_all.py", "--student-id", MSSV, "--seeds", str(SEEDS)], log=f"{OUT}/run_all.log", cwd=LAB)

    run(["tar", "czf", f"{OUT}/lab12_outputs.tar.gz", "evidence", "work/models"], cwd=LAB)
    run(["ls", "-la", OUT])


if __name__ == "__main__":
    main()
