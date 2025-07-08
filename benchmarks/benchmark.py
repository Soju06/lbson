import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path

import psutil
from datasets import ensure_datasets
from environments import ENVIRONMENTS, get_python_executable, setup_environment


def print_system_info() -> None:
    print("=" * 80)
    print("SYSTEM INFORMATION FOR BENCHMARKING")
    print("=" * 80)

    print("\n💻 Operating System")
    print("-" * 40)
    print(f"OS: {platform.system()} {platform.release()}")
    print(f"Platform: {platform.platform()}")
    print(f"Architecture: {platform.machine()}")

    print("\n⚡ CPU Information")
    print("-" * 40)

    try:
        print(f"Physical CPU cores: {psutil.cpu_count(logical=False)}")
        print(f"Logical CPU cores: {psutil.cpu_count(logical=True)}")
    except:
        print("CPU core count: Unable to determine")

    try:
        cpu_freq = psutil.cpu_freq()
        if cpu_freq:
            print(f"CPU frequency: {cpu_freq.current:.0f} MHz")
            print(f"Max CPU frequency: {cpu_freq.max:.0f} MHz")
    except:
        pass

    # Get CPU model name
    if platform.system() == "Darwin":  # macOS
        try:
            result = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True, check=False
            )
            if result.returncode == 0:
                print(f"CPU model: {result.stdout.strip()}")
        except:
            pass
    elif platform.system() == "Linux":
        try:
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if "model name" in line:
                        print(f"CPU model: {line.split(':')[1].strip()}")
                        break
        except:
            pass

    # Memory Information
    print("\n💾 Memory Information")
    print("-" * 40)
    try:
        mem = psutil.virtual_memory()
        print(f"Total memory: {mem.total / (1024**3):.2f} GB")
        print(f"Available memory: {mem.available / (1024**3):.2f} GB")
        print(f"Memory usage: {mem.percent:.1f}%")
    except:
        print("Memory information: Unable to determine")

    try:
        swap = psutil.swap_memory()
        if swap.total > 0:
            print(f"Swap total: {swap.total / (1024**3):.2f} GB")
            print(f"Swap usage: {swap.percent:.1f}%")
    except:
        pass

    # Python Information
    print("\n🐍 Python Environment")
    print("-" * 40)
    print(f"Python version: {platform.python_version()}")
    print(f"Python implementation: {platform.python_implementation()}")
    print(f"Python compiler: {platform.python_compiler()}")

    # Performance-related Information
    print("\n📊 Current Performance Status")
    print("-" * 40)

    # Current CPU usage
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        print(f"Current CPU usage: {cpu_percent:.1f}%")
    except:
        print("CPU usage: Unable to determine")

    # System load average (Unix-like systems)
    if hasattr(os, "getloadavg"):
        try:
            load_avg = os.getloadavg()
            print(f"Load average (1min): {load_avg[0]:.2f}")
            print(f"Load average (5min): {load_avg[1]:.2f}")
            print(f"Load average (15min): {load_avg[2]:.2f}")
        except:
            pass

    # Benchmarking-specific Information
    print("\n🏁 Benchmarking Configuration")
    print("-" * 40)

    # CPU Governor (Linux)
    if platform.system() == "Linux":
        try:
            result = subprocess.run(
                ["cat", "/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                governor = result.stdout.strip()
                print(f"CPU Governor: {governor}")
                if governor != "performance":
                    print("⚠️  Warning: CPU Governor is not set to 'performance'")
        except:
            pass

    # Power status (macOS)
    elif platform.system() == "Darwin":
        try:
            result = subprocess.run(["pmset", "-g", "ps"], capture_output=True, text=True, check=False)
            if result.returncode == 0:
                if "AC Power" in result.stdout:
                    print("Power status: AC Power connected")
                else:
                    print("Power status: Battery power")
                    print("⚠️  Warning: Running on battery power may affect performance")
        except:
            pass

    # Check if system is under load
    try:
        if hasattr(psutil, "cpu_percent"):
            cpu_usage = psutil.cpu_percent(interval=0.1)
            if cpu_usage > 50:
                print(f"⚠️  Warning: High CPU usage detected ({cpu_usage:.1f}%)")

        if hasattr(psutil, "virtual_memory"):
            mem_usage = psutil.virtual_memory().percent
            if mem_usage > 80:
                print(f"⚠️  Warning: High memory usage detected ({mem_usage:.1f}%)")
    except:
        pass


def run_benchmark(selected_envs: list[str] | None = None) -> None:
    print_system_info()
    print("=" * 80)
    print("Running benchmark...")
    print("=" * 80)

    ensure_datasets()

    current_dir = Path(__file__).parent
    results_dir = current_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    environments_to_run = selected_envs or list(ENVIRONMENTS.keys())

    print(f"Running benchmarks for environments: {', '.join(environments_to_run)}")
    print("-" * 80)

    for env_name in environments_to_run:
        if env_name not in ENVIRONMENTS:
            print(f"Warning: Environment '{env_name}' not found. Skipping...")
            continue

        print(f"\nRunning benchmark for environment: {env_name}")
        setup_environment(env_name)
        python = get_python_executable(env_name)
        output_file = results_dir / f"{env_name}.json"

        subprocess.run(
            [
                python,
                str(current_dir / f"runner_{env_name}.py"),
                "-o",
                str(output_file),
                *sys.argv[1:],
            ]
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run lbson benchmarks")
    parser.add_argument(
        "--env",
        choices=list(ENVIRONMENTS.keys()),
        nargs="+",
        help="Specific environment(s) to run benchmarks for. If not specified, runs all environments.",
        metavar="ENV",
    )

    args, unknown_args = parser.parse_known_args()
    sys.argv = [sys.argv[0]] + unknown_args

    run_benchmark(args.env)


if __name__ == "__main__":
    main()
