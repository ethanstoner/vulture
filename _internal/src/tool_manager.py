#!/usr/bin/env python3
"""
Vulture - Tool Manager
Manages downloading and installing decompiler tools and mappings
"""

import os
import sys
import subprocess
import json
import re
import zipfile
import shutil
from pathlib import Path
from typing import Optional, Dict, List
import requests
from urllib.parse import urlparse


class ToolManager:
    """Manages tool downloads and installations."""
    
    def __init__(self, tools_dir: Optional[str] = None):
        # Try to use config for tools_dir
        try:
            from config import Config
            config = Config()
            self.tools_dir = config.get_tools_dir()
        except:
            if tools_dir is None:
                # Try Docker path first, then local
                self.tools_dir = Path("/workspace/tools")
                if not self.tools_dir.exists():
                    self.tools_dir = Path("tools")
            else:
                self.tools_dir = Path(tools_dir)
        
        self.tools_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.tools_dir / "tools_config.json"
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load tool configuration."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            'cfr_version': None,
            'jd_cli_version': None,
            'specialsource_version': None,
            'installed_tools': {}
        }
    
    def _save_config(self):
        """Save tool configuration."""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get_latest_cfr_version(self) -> Optional[str]:
        """Get latest CFR version from GitHub releases."""
        try:
            # Try to get latest release
            response = requests.get(
                "https://api.github.com/repos/leibnitz27/cfr/releases/latest",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                tag = data.get('tag_name', '')
                # Extract version number
                version_match = re.search(r'(\d+\.\d+)', tag)
                if version_match:
                    return version_match.group(1)
            
            # Fallback: try to parse releases page
            response = requests.get(
                "https://api.github.com/repos/leibnitz27/cfr/releases",
                timeout=10
            )
            if response.status_code == 200:
                releases = response.json()
                if releases:
                    tag = releases[0].get('tag_name', '')
                    version_match = re.search(r'(\d+\.\d+)', tag)
                    if version_match:
                        return version_match.group(1)
        except Exception as e:
            print(f"⚠ Could not fetch latest CFR version: {e}")
        
        return "0.152"  # Fallback version
    
    def install_cfr(self, version: Optional[str] = None, force: bool = False) -> bool:
        """Install CFR decompiler."""
        if version is None:
            version = self.get_latest_cfr_version()
        
        cfr_jar = self.tools_dir / "cfr.jar"
        
        # Check if already installed
        if cfr_jar.exists() and not force:
            if self.config.get('installed_tools', {}).get('cfr') == version:
                print(f"✓ CFR {version} already installed")
                return True
        
        print(f"Downloading CFR {version}...")
        
        # Try multiple download URLs
        urls = [
            f"https://github.com/leibnitz27/cfr/releases/latest/download/cfr.jar",
            f"https://github.com/leibnitz27/cfr/releases/download/{version}/cfr-{version}.jar",
            f"https://github.com/leibnitz27/cfr/releases/download/0.152/cfr-0.152.jar",
        ]
        
        for url in urls:
            try:
                response = requests.get(url, timeout=30, stream=True)
                if response.status_code == 200:
                    with open(cfr_jar, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    # Verify it's a valid JAR
                    try:
                        with zipfile.ZipFile(cfr_jar, 'r') as z:
                            z.testzip()
                        print(f"✓ CFR {version} installed successfully")
                        self.config['cfr_version'] = version
                        self.config.setdefault('installed_tools', {})['cfr'] = version
                        self._save_config()
                        return True
                    except:
                        print(f"⚠ Downloaded file is not a valid JAR, trying next URL...")
                        cfr_jar.unlink()
                        continue
            except Exception as e:
                print(f"⚠ Failed to download from {url}: {e}")
                continue
        
        print(f"✗ Failed to install CFR {version}")
        return False
    
    def install_jd_cli(self, version: str = "1.2.0", force: bool = False) -> bool:
        """Install JD-CLI decompiler."""
        jd_cli_jar = self.tools_dir / "jd-cli.jar"
        
        # Check if already installed
        if jd_cli_jar.exists() and not force:
            if self.config.get('installed_tools', {}).get('jd_cli') == version:
                print(f"✓ JD-CLI {version} already installed")
                return True
        
        print(f"Downloading JD-CLI {version}...")
        
        urls = [
            f"https://github.com/intoolswetrust/jd-cli/releases/download/jd-cli-{version}/jd-cli-{version}-dist.tar.gz",
        ]
        
        for url in urls:
            try:
                response = requests.get(url, timeout=30, stream=True)
                if response.status_code == 200:
                    tar_path = self.tools_dir / "jd-cli.tar.gz"
                    with open(tar_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    # Extract JAR from tarball
                    try:
                        import tarfile
                        import tempfile
                        with tarfile.open(tar_path, 'r:gz') as tar:
                            # Find the JAR file in the archive
                            for member in tar.getmembers():
                                if member.name.endswith('.jar') and 'jd-cli' in member.name:
                                    tar.extract(member, self.tools_dir)
                                    extracted_jar = self.tools_dir / member.name.split('/')[-1]
                                    if extracted_jar.exists():
                                        shutil.move(str(extracted_jar), str(jd_cli_jar))
                                        break
                        
                        tar_path.unlink()
                        
                        if jd_cli_jar.exists():
                            print(f"✓ JD-CLI {version} installed successfully")
                            self.config['jd_cli_version'] = version
                            self.config.setdefault('installed_tools', {})['jd_cli'] = version
                            self._save_config()
                            return True
                    except Exception as e:
                        print(f"⚠ Failed to extract JD-CLI: {e}")
                        if tar_path.exists():
                            tar_path.unlink()
                        continue
            except Exception as e:
                print(f"⚠ Failed to download from {url}: {e}")
                continue
        
        print(f"✗ Failed to install JD-CLI {version}")
        return False
    
    def install_specialsource(self, version: str = "1.11.0", force: bool = False) -> bool:
        """Install SpecialSource for applying mappings."""
        specialsource_jar = self.tools_dir / "specialsource.jar"
        
        # Check if already installed
        if specialsource_jar.exists() and not force:
            if self.config.get('installed_tools', {}).get('specialsource') == version:
                print(f"✓ SpecialSource {version} already installed")
                return True
        
        print(f"Downloading SpecialSource {version}...")
        
        urls = [
            f"https://github.com/md-5/SpecialSource/releases/download/{version}/SpecialSource-{version}-shaded.jar",
            f"https://repo.md-5.net/content/repositories/releases/net/md-5/SpecialSource/{version}/SpecialSource-{version}-shaded.jar",
        ]
        
        for url in urls:
            try:
                response = requests.get(url, timeout=30, stream=True)
                if response.status_code == 200:
                    with open(specialsource_jar, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    # Verify it's a valid JAR
                    try:
                        with zipfile.ZipFile(specialsource_jar, 'r') as z:
                            z.testzip()
                        print(f"✓ SpecialSource {version} installed successfully")
                        self.config['specialsource_version'] = version
                        self.config.setdefault('installed_tools', {})['specialsource'] = version
                        self._save_config()
                        return True
                    except:
                        print(f"⚠ Downloaded file is not a valid JAR, trying next URL...")
                        specialsource_jar.unlink()
                        continue
            except Exception as e:
                print(f"⚠ Failed to download from {url}: {e}")
                continue
        
        print(f"✗ Failed to install SpecialSource {version}")
        return False
    
    def ensure_all_tools(self, force: bool = False):
        """Ensure all required tools are installed."""
        print("Checking tool installations...")
        print("=" * 60)
        
        self.install_cfr(force=force)
        self.install_jd_cli(force=force)
        self.install_specialsource(force=force)
        
        print("=" * 60)
        print("Tool installation check complete!")
        print()


class MappingsDownloader:
    """Downloads Minecraft version mappings."""
    
    def __init__(self, mappings_dir: Optional[str] = None):
        # Try to use config for mappings_dir
        try:
            from config import Config
            config = Config()
            self.mappings_dir = config.get_mappings_dir()
        except:
            if mappings_dir is None:
                # Try Docker path first, then local
                self.mappings_dir = Path("/workspace/mappings")
                if not self.mappings_dir.exists():
                    self.mappings_dir = Path("mappings")
            else:
                self.mappings_dir = Path(mappings_dir)
        
        self.mappings_dir.mkdir(parents=True, exist_ok=True)
    
    def download_mcp_mappings(self, mc_version: str) -> Optional[Path]:
        """Download MCP mappings for a Minecraft version from MCPBot."""
        print(f"Downloading MCP mappings for Minecraft {mc_version}...")
        
        # MCPBot export URL format
        url = f"http://export.mcpbot.bspk.rs/mcp_snapshot/{mc_version}/mcp_snapshot-{mc_version}.zip"
        
        zip_path = self.mappings_dir / f"mcp_snapshot-{mc_version}.zip"
        extract_dir = self.mappings_dir / f"mcp-{mc_version}"
        
        # Check if already downloaded
        if extract_dir.exists() and (extract_dir / "joined.srg").exists():
            print(f"✓ MCP mappings for {mc_version} already exist")
            return extract_dir / "joined.srg"
        
        try:
            response = requests.get(url, timeout=60, stream=True)
            if response.status_code == 200:
                with open(zip_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Extract ZIP
                with zipfile.ZipFile(zip_path, 'r') as z:
                    z.extractall(extract_dir)
                
                # Find joined.srg
                srg_file = extract_dir / "joined.srg"
                if srg_file.exists():
                    print(f"✓ MCP mappings for {mc_version} downloaded successfully")
                    zip_path.unlink()  # Clean up ZIP
                    return srg_file
                else:
                    # Look for any .srg file
                    srg_files = list(extract_dir.rglob("*.srg"))
                    if srg_files:
                        print(f"✓ MCP mappings for {mc_version} downloaded (using {srg_files[0].name})")
                        zip_path.unlink()
                        return srg_files[0]
            else:
                print(f"⚠ MCPBot returned status {response.status_code} for version {mc_version}")
        except Exception as e:
            print(f"⚠ Failed to download MCP mappings: {e}")
        
        if zip_path.exists():
            zip_path.unlink()
        
        return None
    
    def download_forge_mappings(self, mc_version: str) -> Optional[Path]:
        """Download Forge mappings for a Minecraft version."""
        print(f"Attempting to download Forge mappings for Minecraft {mc_version}...")
        print("⚠ Forge mappings require manual download from https://files.minecraftforge.net/")
        print("   Look for *-mappings.zip files for your version")
        return None
    
    def get_mappings(self, mc_version: str, prefer_mcp: bool = True) -> Optional[Path]:
        """Get mappings for a Minecraft version, trying multiple sources."""
        if prefer_mcp:
            mappings = self.download_mcp_mappings(mc_version)
            if mappings:
                return mappings
        
        # Try Forge mappings as fallback
        mappings = self.download_forge_mappings(mc_version)
        if mappings:
            return mappings
        
        # Check if mappings already exist locally
        local_srg = self.mappings_dir / f"mcp-{mc_version}" / "joined.srg"
        if local_srg.exists():
            return local_srg
        
        # Check for any .srg file in mappings directory
        srg_files = list(self.mappings_dir.glob("*.srg"))
        if srg_files:
            print(f"⚠ Using existing mappings file: {srg_files[0].name}")
            return srg_files[0]
        
        return None


def main():
    """CLI for tool manager."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Vulture Tool Manager")
    parser.add_argument('--install-tools', action='store_true', help='Install all tools')
    parser.add_argument('--install-cfr', action='store_true', help='Install CFR decompiler')
    parser.add_argument('--install-jd-cli', action='store_true', help='Install JD-CLI decompiler')
    parser.add_argument('--install-specialsource', action='store_true', help='Install SpecialSource')
    parser.add_argument('--download-mappings', type=str, metavar='VERSION', help='Download mappings for Minecraft version')
    parser.add_argument('--force', action='store_true', help='Force reinstall even if already installed')
    parser.add_argument('--tools-dir', type=str, help='Tools directory path')
    parser.add_argument('--mappings-dir', type=str, help='Mappings directory path')
    
    args = parser.parse_args()
    
    if args.install_tools or args.install_cfr or args.install_jd_cli or args.install_specialsource:
        manager = ToolManager(args.tools_dir)
        
        if args.install_tools:
            manager.ensure_all_tools(force=args.force)
        else:
            if args.install_cfr:
                manager.install_cfr(force=args.force)
            if args.install_jd_cli:
                manager.install_jd_cli(force=args.force)
            if args.install_specialsource:
                manager.install_specialsource(force=args.force)
    
    if args.download_mappings:
        downloader = MappingsDownloader(args.mappings_dir)
        mappings = downloader.get_mappings(args.download_mappings)
        if mappings:
            print(f"✓ Mappings available at: {mappings}")
        else:
            print(f"✗ Failed to download mappings for {args.download_mappings}")
            sys.exit(1)


if __name__ == '__main__':
    main()
