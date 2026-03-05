"""
PPW build script.

How secrets are baked in:
  1. Reads MONGO_URI from env (GitHub Actions secrets) or .env
  2. Writes config_frozen.py with the URI hardcoded inside
  3. PyInstaller bundles it - the EXE imports config_frozen instead of config
  4. config_frozen.py is deleted after the build
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
    has_icon = (ROOT / "extension" / "icons" / "icon.ico").exists()
    icon_line = "    icon='" + str(ROOT / 'extension' / 'icons' / 'icon.ico') + "',\n" if has_icon else "    icon=None,\n"
    spec_text = (
        "block_cipher = None\n"
        "a = Analysis(\n"
        "    ['main.py'],\n"
        "    pathex=[],\n"
        "    binaries=[],\n"
        "    datas=[],\n"
        "    hiddenimports=[\n"
        "        'config_frozen',\n"
        "        'pymongo', 'pymongo.srv', 'pymongo.monitoring',\n"
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
        + icon_line +
        ")\n"
    )
    SPEC.write_text(spec_text, encoding="utf-8")
    print("[OK] ppw.spec written")


def build():
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
        exe = DIST / "PPW-PasswordManager"
    if exe.exists():
        mb = round(exe.stat().st_size / 1_048_576, 1)
        print("[OK] " + str(exe) + " (" + str(mb) + " MB)")
    else:
        print("[ERROR] EXE not found")


if __name__ == "__main__":
    try:
        write_frozen_config()
        write_spec()
        build()
    finally:
        delete_frozen_config()

