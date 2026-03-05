"""
PPW build script.
Produces: dist/PPW-PasswordManager.exe  (via PyInstaller)
          dist/PPW-Setup.exe             (via Inno Setup)
"""
import os
import sys
import subprocess
from pathlib import Path

ROOT   = Path(__file__).parent
DIST   = ROOT / "dist"
BUILD  = ROOT / "build_tmp"
SPEC   = ROOT / "ppw.spec"
FROZEN = ROOT / "config_frozen.py"
ISS    = ROOT / "installer.iss"

ISCC_PATHS = [
    r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    r"C:\Program Files\Inno Setup 6\ISCC.exe",
    r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
]


def get_secret(name):
    val = os.environ.get(name, "")
    if not val:
        env_path = ROOT / ".env"
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                if k.strip() == name:
                    val = v.strip()
                    break
    return val


MONGO_URI     = get_secret("MONGO_URI")
DATABASE_NAME = get_secret("DATABASE_NAME") or "password_manager"

if not MONGO_URI:
    sys.exit("ERROR: MONGO_URI is not set.")


def write_frozen_config():
    content = (
        "# AUTO-GENERATED - DO NOT COMMIT - deleted after build\n"
        "from datetime import timedelta\n"
        "\n"
        "APP_NAME = 'PPW'\n"
        "VERSION  = '1.0.0'\n"
        "\n"
        "MONGO_URI     = " + repr(MONGO_URI) + "\n"
        "DATABASE_NAME = " + repr(DATABASE_NAME) + "\n"
        "\n"
        "COLLECTION_MASTER     = 'master_password'\n"
        "COLLECTION_ACCOUNTS   = 'accounts'\n"
        "COLLECTION_LOGS       = 'activity_logs'\n"
        "COLLECTION_CATEGORIES = 'categories'\n"
        "\n"
        "PASSWORD_MIN_LENGTH        = 8\n"
        "MASTER_PASSWORD_MIN_LENGTH = 12\n"
        "SESSION_TIMEOUT            = timedelta(minutes=15)\n"
        "MAX_LOGIN_ATTEMPTS         = 5\n"
        "LOCKOUT_DURATION           = timedelta(minutes=30)\n"
        "PBKDF2_ITERATIONS          = 100000\n"
        "ENCRYPTION_ALGORITHM       = 'AES-256-GCM'\n"
    )
    FROZEN.write_text(content, encoding="utf-8")
    print("[OK] config_frozen.py written")


def delete_frozen_config():
    if FROZEN.exists():
        FROZEN.unlink()
    print("[OK] config_frozen.py deleted")


def write_spec():
    spec_text = (
        "block_cipher = None\n"
        "a = Analysis(\n"
        "    ['main.py'],\n"
        "    pathex=[],\n"
        "    binaries=[],\n"
        "    datas=[],\n"
        "    hiddenimports=[\n"
        "        'config_frozen',\n"
        "        'pymongo', 'pymongo.monitoring',\n"
        "        'dns', 'dns.resolver',\n"
        "        'cryptography',\n"
        "        'cryptography.hazmat.primitives.ciphers.aead',\n"
        "        'PyQt6', 'PyQt6.QtWidgets', 'PyQt6.QtCore', 'PyQt6.QtGui',\n"
        "        'pyperclip', 'dotenv',\n"
        "    ],\n"
        "    hookspath=[],\n"
        "    runtime_hooks=[],\n"
        "    excludes=['tkinter', 'matplotlib', 'numpy', 'scipy'],\n"
        "    cipher=block_cipher,\n"
        "    noarchive=False,\n"
        ")\n"
        "pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)\n"
        "exe = EXE(\n"
        "    pyz, a.scripts, a.binaries, a.zipfiles, a.datas, [],\n"
        "    name='PPW-PasswordManager',\n"
        "    debug=False, strip=False, upx=True, console=False,\n"
        "    icon=None,\n"
        ")\n"
    )
    SPEC.write_text(spec_text, encoding="utf-8")
    print("[OK] ppw.spec written")


def build_exe():
    print("-- Installing PyInstaller --")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "pyinstaller>=6.0", "-q"]
    )
    print("-- Running PyInstaller --")
    subprocess.check_call([
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--distpath", str(DIST),
        "--workpath", str(BUILD),
        str(SPEC),
    ])
    exe = DIST / "PPW-PasswordManager.exe"
    if not exe.exists():
        sys.exit("[ERROR] EXE not found after PyInstaller")
    mb = round(exe.stat().st_size / 1_048_576, 1)
    print("[OK] EXE: " + str(exe) + " (" + str(mb) + " MB)")


def find_iscc():
    for path in ISCC_PATHS:
        if Path(path).exists():
            return path
    return None


def build_installer():
    iscc = find_iscc()
    if iscc is None:
        print("-- Inno Setup not found, installing via choco --")
        subprocess.check_call(
            ["choco", "install", "innosetup", "--yes", "--no-progress"],
            stdout=subprocess.DEVNULL,
        )
        iscc = find_iscc()

    if iscc is None:
        sys.exit("[ERROR] Inno Setup not found even after choco install")

    print("-- Running Inno Setup --")
    subprocess.check_call([iscc, str(ISS)])

    setup = DIST / "PPW-Setup.exe"
    if setup.exists():
        mb = round(setup.stat().st_size / 1_048_576, 1)
        print("[OK] Installer: " + str(setup) + " (" + str(mb) + " MB)")
    else:
        sys.exit("[ERROR] PPW-Setup.exe not found after Inno Setup")


if __name__ == "__main__":
    write_frozen_config()
    write_spec()
    try:
        build_exe()
        build_installer()
    finally:
        delete_frozen_config()

