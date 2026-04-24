#!/usr/bin/env python3
"""Install Bitwarden CLI if not already installed."""

import os
import platform
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path


def check_bw_installed():
    """Check if Bitwarden CLI is already installed."""
    return shutil.which("bw") is not None


def get_bw_version():
    """Get the version of installed Bitwarden CLI."""
    try:
        result = subprocess.run(
            ["bw", "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def install_bitwarden_cli():
    """Install Bitwarden CLI."""
    if check_bw_installed():
        version = get_bw_version()
        print(f"✓ Bitwarden CLI is already installed: {version}")
        return True

    print("Installing Bitwarden CLI...")

    # Try npm first (recommended method)
    if shutil.which("npm"):
        print("Using npm to install Bitwarden CLI...")
        try:
            subprocess.run(
                ["npm", "install", "-g", "@bitwarden/cli"],
                capture_output=True,
                text=True,
                check=True,
            )
            if check_bw_installed():
                version = get_bw_version()
                print(f"✓ Bitwarden CLI installed via npm: {version}")
                return True
        except subprocess.CalledProcessError as e:
            print(f"⚠ npm installation failed: {e.stderr}")
            print("Trying alternative installation method...")

    # Fallback: Direct download from GitHub
    system = platform.system().lower()
    machine = platform.machine().lower()

    arch_map = {
        "x86_64": "x64",
        "amd64": "x64",
        "aarch64": "arm64",
        "arm64": "arm64",
    }
    arch = arch_map.get(machine, machine)

    if system not in ["linux", "darwin", "windows"]:
        print(f"Error: Unsupported OS: {system}")
        return False

    if arch not in ["x64", "arm64"]:
        print(f"Error: Unsupported architecture: {arch}")
        return False

    bw_version = "2024.9.0"
    if system == "windows":
        ext = "zip"
        exe_ext = ".exe"
        platform_name = "win"
    elif system == "darwin":
        ext = "zip"
        exe_ext = ""
        platform_name = "macos"
    else:
        ext = "zip"
        exe_ext = ""
        platform_name = "linux"

    url_formats = [
        f"https://github.com/bitwarden/clients/releases/download/cli-v{bw_version}"
        f"/bw-{platform_name}-{arch}-{bw_version}.{ext}",
        f"https://vault.bitwarden.com/download/?app=cli&platform={platform_name}",
    ]

    with tempfile.TemporaryDirectory() as tmp_dir:
        zip_path = os.path.join(tmp_dir, "bw-cli.zip")

        downloaded = False
        for bw_url in url_formats:
            print(f"Trying to download from {bw_url}...")
            try:
                urllib.request.urlretrieve(bw_url, zip_path)
                if os.path.getsize(zip_path) > 1000:
                    downloaded = True
                    break
            except Exception as e:
                print(f"  Failed: {e}")
                continue

        if not downloaded:
            print("Error: Could not download Bitwarden CLI from any source.")
            print("Please install manually:")
            print("  npm install -g @bitwarden/cli")
            print("  or")
            print("  Visit: https://bitwarden.com/help/article/cli/#download-and-install")
            return False

        extract_dir = os.path.join(tmp_dir, "extracted")
        os.makedirs(extract_dir, exist_ok=True)

        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(extract_dir)
        except Exception as e:
            print(f"Error extracting archive: {e}")
            return False

        bw_binary = None
        for root, _, files in os.walk(extract_dir):
            for file in files:
                if file == f"bw{exe_ext}":
                    bw_binary = os.path.join(root, file)
                    break
                elif file.startswith("bw") and (file.endswith(exe_ext) or not exe_ext):
                    potential_binary = os.path.join(root, file)
                    if os.access(potential_binary, os.X_OK) or system == "windows":
                        bw_binary = potential_binary
                        break
            if bw_binary:
                break

        if not bw_binary or not os.path.exists(bw_binary):
            print("Error: Could not find bw binary in archive")
            return False

        if system != "windows":
            os.chmod(bw_binary, 0o755)

        install_dir = None
        if system == "windows":
            for path in [
                os.path.join(os.environ.get("PROGRAMFILES", ""), "Bitwarden CLI"),
                os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Bitwarden CLI"),
            ]:
                if os.path.exists(os.path.dirname(path)) or path.startswith(os.environ.get("LOCALAPPDATA", "")):
                    install_dir = path
                    os.makedirs(install_dir, exist_ok=True)
                    break
        else:
            local_bin = Path.home() / ".local" / "bin"
            if local_bin.exists() or not os.access("/usr/local/bin", os.W_OK):
                install_dir = str(local_bin)
                local_bin.mkdir(parents=True, exist_ok=True)
            else:
                install_dir = "/usr/local/bin"

        if not install_dir:
            print("Error: Could not determine installation directory")
            return False

        install_path = os.path.join(install_dir, f"bw{exe_ext}")
        shutil.copy2(bw_binary, install_path)

        if system != "windows":
            os.chmod(install_path, 0o755)

        print(f"✓ Bitwarden CLI installed to {install_path}")

        if check_bw_installed():
            version = get_bw_version()
            print(f"✓ Installation successful: {version}")
            return True
        else:
            print("⚠ Warning: Bitwarden CLI installed but not in PATH")
            print(f"  Add {install_dir} to your PATH")
            return False


if __name__ == "__main__":
    success = install_bitwarden_cli()
    sys.exit(0 if success else 1)
