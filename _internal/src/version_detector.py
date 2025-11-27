#!/usr/bin/env python3
"""
Vulture - Version Detector
Detects Minecraft version from mod JAR files
"""

import zipfile
import json
import re
from pathlib import Path
from typing import Optional, List


class VersionDetector:
    """Detects Minecraft version from mod JAR files."""
    
    # Common version patterns
    VERSION_PATTERNS = [
        r'(\d+\.\d+(?:\.\d+)?)',  # Standard version format
        r'mc(\d+\.\d+(?:\.\d+)?)',  # mc1.8.9 format
        r'(\d+\.\d+\.\d+)',  # Full version
    ]
    
    # Known Minecraft versions (for validation)
    KNOWN_VERSIONS = [
        "1.7.10", "1.8", "1.8.9", "1.9", "1.9.4", "1.10", "1.10.2",
        "1.11", "1.11.2", "1.12", "1.12.2", "1.13", "1.13.2",
        "1.14", "1.14.4", "1.15", "1.15.2", "1.16", "1.16.1", "1.16.5",
        "1.17", "1.17.1", "1.18", "1.18.1", "1.18.2", "1.19", "1.19.2",
        "1.19.3", "1.19.4", "1.20", "1.20.1", "1.20.2", "1.20.4", "1.20.6",
        "1.21", "1.21.1"
    ]
    
    def __init__(self, jar_path: str):
        self.jar_path = Path(jar_path)
        if not self.jar_path.exists():
            raise FileNotFoundError(f"JAR file not found: {jar_path}")
        
        self.jar = zipfile.ZipFile(self.jar_path, 'r')
    
    def detect_from_filename(self) -> Optional[str]:
        """Try to detect version from JAR filename."""
        filename = self.jar_path.stem.lower()
        
        # Look for version patterns in filename
        for pattern in self.VERSION_PATTERNS:
            match = re.search(pattern, filename)
            if match:
                version = match.group(1)
                # Normalize version (e.g., "1.8" -> "1.8.9" if close match)
                normalized = self._normalize_version(version)
                if normalized:
                    return normalized
        
        return None
    
    def detect_from_mcmod_info(self) -> Optional[str]:
        """Detect version from mcmod.info file."""
        if 'mcmod.info' not in self.jar.namelist():
            return None
        
        try:
            info_content = self.jar.read('mcmod.info').decode('utf-8')
            
            # Try to parse as JSON
            try:
                mod_info = json.loads(info_content)
                if isinstance(mod_info, list) and len(mod_info) > 0:
                    mod_info = mod_info[0]
                
                # Check for mcversion field
                if 'mcversion' in mod_info:
                    version = str(mod_info['mcversion'])
                    normalized = self._normalize_version(version)
                    if normalized:
                        return normalized
            except:
                pass
            
            # Try regex search in raw content
            for pattern in self.VERSION_PATTERNS:
                match = re.search(pattern, info_content)
                if match:
                    version = match.group(1)
                    normalized = self._normalize_version(version)
                    if normalized:
                        return normalized
        except:
            pass
        
        return None
    
    def detect_from_manifest(self) -> Optional[str]:
        """Detect version from MANIFEST.MF."""
        manifest_paths = [
            'META-INF/MANIFEST.MF',
            'META-INF/maven/**/pom.properties',
        ]
        
        for path_pattern in manifest_paths:
            for file_path in self.jar.namelist():
                if 'MANIFEST.MF' in file_path or 'pom.properties' in file_path:
                    try:
                        content = self.jar.read(file_path).decode('utf-8', errors='ignore')
                        for pattern in self.VERSION_PATTERNS:
                            match = re.search(pattern, content)
                            if match:
                                version = match.group(1)
                                normalized = self._normalize_version(version)
                                if normalized:
                                    return normalized
                    except:
                        continue
        
        return None
    
    def detect_from_class_files(self) -> Optional[str]:
        """Try to detect version from class file names/packages."""
        # Look for version-specific packages
        version_indicators = {
            'net.minecraft.client': '1.8+',
            'net.minecraftforge': '1.7.10+',
        }
        
        class_files = [f for f in self.jar.namelist() if f.endswith('.class')]
        
        # Check package structure for version hints
        for class_file in class_files[:100]:  # Check first 100 classes
            for indicator, version_hint in version_indicators.items():
                if indicator.replace('.', '/') in class_file:
                    # This is a rough indicator, return a common version
                    return "1.8.9"  # Default fallback
        
        return None
    
    def _normalize_version(self, version: str) -> Optional[str]:
        """Normalize version string to standard format."""
        # Remove 'mc' prefix if present
        version = re.sub(r'^mc', '', version, flags=re.IGNORECASE)
        
        # Ensure we have at least major.minor
        parts = version.split('.')
        if len(parts) < 2:
            return None
        
        # Try to match to known versions
        major_minor = f"{parts[0]}.{parts[1]}"
        
        # Find closest match in known versions
        for known_version in self.KNOWN_VERSIONS:
            if known_version.startswith(major_minor):
                return known_version
        
        # If no exact match, return normalized version
        if len(parts) == 2:
            # Try to find a common patch version
            for known_version in self.KNOWN_VERSIONS:
                if known_version.startswith(major_minor):
                    return known_version
        
        # Return as-is if it looks valid
        if re.match(r'^\d+\.\d+(?:\.\d+)?$', version):
            return version
        
        return None
    
    def detect(self) -> Optional[str]:
        """Detect Minecraft version using all available methods."""
        methods = [
            self.detect_from_mcmod_info,
            self.detect_from_filename,
            self.detect_from_manifest,
            self.detect_from_class_files,
        ]
        
        for method in methods:
            try:
                version = method()
                if version:
                    return version
            except Exception as e:
                continue
        
        return None
    
    def close(self):
        """Close the JAR file."""
        self.jar.close()


def main():
    """CLI for version detection."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python version_detector.py <mod.jar>")
        sys.exit(1)
    
    jar_path = sys.argv[1]
    
    try:
        detector = VersionDetector(jar_path)
        version = detector.detect()
        detector.close()
        
        if version:
            print(f"Detected Minecraft version: {version}")
            sys.exit(0)
        else:
            print("Could not detect Minecraft version")
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
