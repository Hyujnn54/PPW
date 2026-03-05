"""
Version information
"""

__version__ = "1.0.0"
__author__ = "PPW Team"
__license__ = "MIT"
__description__ = "Personal Password Manager - Secure, encrypted password storage"
__url__ = "https://github.com/yourusername/PPW"

# Version components
VERSION_MAJOR = 1
VERSION_MINOR = 0
VERSION_PATCH = 0
VERSION_INFO = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)

# Build information
BUILD_DATE = "2026-03-05"
BUILD_TYPE = "release"  # release, beta, alpha, dev

def get_version_string():
    """Get full version string"""
    version = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}"
    if BUILD_TYPE != "release":
        version += f"-{BUILD_TYPE}"
    return version

def get_full_version():
    """Get full version with build info"""
    return f"PPW Password Manager v{get_version_string()} ({BUILD_DATE})"

