import os
import subprocess
import sys

# PiSugar setup
PISUGAR_SERVICE = "pisugar-server"
PISUGAR_VERSION = "2.0.0-1"
CHANNEL = "release"

# Paths for storing .deb files
PISUGAR_LIB_DIR = "/opt/infoHUD/lib/"
PISUGAR_SERVER_DEB = os.path.join(PISUGAR_LIB_DIR, "pisugar-server.deb")
PISUGAR_POWEROFF_DEB = os.path.join(PISUGAR_LIB_DIR, "pisugar-poweroff.deb")
PISUGAR_PROGRAMMER_DEB = os.path.join(PISUGAR_LIB_DIR, "pisugar-programmer.deb")

SYSTEMD_SERVICE_FILE = "/opt/infoHUD/systemd/pisugar-server.service"
SYSTEMD_TARGET_PATH = "/etc/systemd/system/pisugar-server.service"
DEBIAN_FRONTEND = "DEBIAN_FRONTEND=noninteractive"
PISUGAR_PASSWORD = "admin"

# Required system packages
SYSTEM_PACKAGES = [
    "python3-pip",
    "python3-pil",
    "python3-numpy",
    "python3-gpiozero",
    "i2c-tools", 
    "debconf-utils"  
]

# Required Python packages
PYTHON_PACKAGES = ["spidev"]


def is_installed(package):
    """Check if a system package is installed."""
    try:
        subprocess.run(["dpkg", "-s", package], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def install_system_packages():
    """Ensure all required system packages are installed."""
    missing_packages = [pkg for pkg in SYSTEM_PACKAGES if not is_installed(pkg)]

    if missing_packages:
        print(f"📦 Installing missing system packages: {', '.join(missing_packages)}")
        subprocess.run(["sudo", "apt-get", "install", "-y"] + missing_packages, check=True)
    else:
        print("✅ All system packages are already installed.")


def is_python_package_installed(package):
    """Check if a Python package is installed."""
    return subprocess.run([sys.executable, "-c", f"import {package}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0


def install_python_packages():
    """Ensure all required Python packages are installed."""
    missing_packages = [pkg for pkg in PYTHON_PACKAGES if not is_python_package_installed(pkg)]

    if missing_packages:
        print(f"🐍 Installing missing Python packages: {', '.join(missing_packages)}")
        subprocess.run([sys.executable, "-m", "pip", "install"] + missing_packages, check=True)
    else:
        print("✅ All Python packages are already installed.")


def get_architecture():
    """Detects system architecture (armhf for 32-bit, arm64 for 64-bit)."""
    return "arm64" if os.uname().machine == "aarch64" else "armhf"


def get_pisugar_urls():
    """Constructs the correct PiSugar package URLs based on version, arch, and channel."""
    arch = get_architecture()

    package_server = f"pisugar-server_{PISUGAR_VERSION}_{arch}.deb"
    package_poweroff = f"pisugar-poweroff_{PISUGAR_VERSION}_{arch}.deb"
    package_programmer = f"pisugar-programmer_{PISUGAR_VERSION}_{arch}.deb"

    pisugar_server_url = f"http://cdn.pisugar.com/{CHANNEL}/{package_server}"
    pisugar_poweroff_url = f"http://cdn.pisugar.com/{CHANNEL}/{package_poweroff}"
    pisugar_programmer_url = f"http://cdn.pisugar.com/{CHANNEL}/{package_programmer}"

    return pisugar_server_url, pisugar_poweroff_url, pisugar_programmer_url


def download_pisugar_debs():
    """Download the PiSugar .deb files if they are missing."""
    pisugar_server_url, pisugar_poweroff_url, pisugar_programmer_url = get_pisugar_urls()

    os.makedirs(PISUGAR_LIB_DIR, exist_ok=True)  # Ensure the lib folder exists

    if not os.path.isfile(PISUGAR_SERVER_DEB):
        print(f"⬇️ Downloading PiSugar Server: {pisugar_server_url}")
        subprocess.run(["wget", "-O", PISUGAR_SERVER_DEB, pisugar_server_url], check=True)

    if not os.path.isfile(PISUGAR_POWEROFF_DEB):
        print(f"⬇️ Downloading PiSugar Poweroff: {pisugar_poweroff_url}")
        subprocess.run(["wget", "-O", PISUGAR_POWEROFF_DEB, pisugar_poweroff_url], check=True)

    if not os.path.isfile(PISUGAR_PROGRAMMER_DEB):
        print(f"⬇️ Downloading PiSugar Programmer: {pisugar_programmer_url}")
        subprocess.run(["wget", "-O", PISUGAR_PROGRAMMER_DEB, pisugar_programmer_url], check=True)


def is_pisugar_installed():
    """Check if the PiSugar server is installed and running."""
    try:
        subprocess.run(["systemctl", "is-active", "--quiet", PISUGAR_SERVICE], check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def install_pisugar():
    """Install PiSugar non-interactively using .deb files."""
    if is_pisugar_installed():
        print("✅ PiSugar server is already installed and running.")
        return

    # Ensure all required system packages are installed
    install_system_packages()

    # Set debconf selections for PiSugar
    debconf_cmds = f"""
echo 'pisugar-server pisugar-server/model select PiSugar 3' | sudo debconf-set-selections
echo 'pisugar-server pisugar-server/auth-username string admin' | sudo debconf-set-selections
echo 'pisugar-server pisugar-server/auth-password password {PISUGAR_PASSWORD}' | sudo debconf-set-selections
echo 'pisugar-poweroff pisugar-poweroff/model select PiSugar 3' | sudo debconf-set-selections
"""
    subprocess.run(["bash", "-c", debconf_cmds], check=True)

    # Download any missing .deb files
    download_pisugar_debs()

    # Install PiSugar packages using dpkg in non-interactive mode
    print("📦 Installing PiSugar packages...")
    subprocess.run(["sudo", "DEBIAN_FRONTEND=noninteractive", "dpkg", "-i", PISUGAR_SERVER_DEB], check=True)
    subprocess.run(["sudo", "DEBIAN_FRONTEND=noninteractive", "dpkg", "-i", PISUGAR_POWEROFF_DEB], check=True)
    subprocess.run(["sudo", "DEBIAN_FRONTEND=noninteractive", "dpkg", "-i", PISUGAR_PROGRAMMER_DEB], check=True)

    # Fix missing dependencies
    subprocess.run(["sudo", "apt-get", "-f", "install", "-y"], check=True)

    # Enable and start PiSugar service
    subprocess.run(["sudo", "systemctl", "enable", PISUGAR_SERVICE], check=True)
    subprocess.run(["sudo", "systemctl", "start", PISUGAR_SERVICE], check=True)

    print("✅ PiSugar installed successfully (no confirmation prompt).")


def main():
    """Run setup checks before starting infoHUD."""
    print("🚀 Running infoHUD setup checks...")
    install_python_packages()
    install_pisugar()
    print("✅ Setup complete!")


if __name__ == "__main__":
    main()
