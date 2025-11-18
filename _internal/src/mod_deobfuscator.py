#!/usr/bin/env python3
"""
Vulture - Minecraft Mod Deobfuscator
Decompiles and deobfuscates Minecraft mod JAR files using MCP mappings

This tool:
1. Decompiles JAR files
2. Applies MCP mappings to restore readable names
3. Analyzes the deobfuscated code
"""

import zipfile
import subprocess
import json
import re
import os
import sys
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests
from urllib.parse import urlparse


class MCPMappingLoader:
    """Loads and manages MCP mappings."""
    
    def __init__(self, mc_version: str = "1.8.9"):
        self.mc_version = mc_version
        self.mappings = {
            'classes': {},
            'methods': {},
            'fields': {}
        }
        self.reverse_mappings = {
            'classes': {},
            'methods': {},
            'fields': {}
        }
    
    def load_from_srg(self, srg_file: str):
        """Load mappings from SRG file format."""
        print(f"Loading mappings from {srg_file}...")
        
        with open(srg_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split()
                if len(parts) < 3:
                    continue
                
                if line.startswith('CL:'):  # Class mapping
                    # Format: CL: obfuscated mapped
                    obf = parts[1]
                    mapped = parts[2]
                    self.mappings['classes'][obf] = mapped
                    self.reverse_mappings['classes'][mapped] = obf
                
                elif line.startswith('MD:'):  # Method mapping
                    # Format: MD: obf_class obf_method obf_desc mapped_class mapped_method mapped_desc
                    if len(parts) >= 6:
                        obf_class = parts[1]
                        obf_method = parts[2]
                        mapped_class = parts[4]
                        mapped_method = parts[5]
                        
                        key = f"{obf_class}.{obf_method}"
                        value = f"{mapped_class}.{mapped_method}"
                        self.mappings['methods'][key] = value
                        self.reverse_mappings['methods'][value] = key
                
                elif line.startswith('FD:'):  # Field mapping
                    # Format: FD: obf_class/obf_field mapped_class/mapped_field
                    if len(parts) >= 3:
                        obf_full = parts[1]
                        mapped_full = parts[2]
                        
                        self.mappings['fields'][obf_full] = mapped_full
                        self.reverse_mappings['fields'][mapped_full] = obf_full
        
        print(f"Loaded {len(self.mappings['classes'])} class mappings")
        print(f"Loaded {len(self.mappings['methods'])} method mappings")
        print(f"Loaded {len(self.mappings['fields'])} field mappings")
    
    def load_from_csv(self, csv_file: str):
        """Load mappings from CSV format."""
        import csv
        
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Adjust based on CSV format
                if 'obfuscated' in row and 'mapped' in row:
                    obf = row['obfuscated']
                    mapped = row['mapped']
                    mapping_type = row.get('type', 'class')
                    
                    if mapping_type == 'class':
                        self.mappings['classes'][obf] = mapped
                    elif mapping_type == 'method':
                        self.mappings['methods'][obf] = mapped
                    elif mapping_type == 'field':
                        self.mappings['fields'][obf] = mapped
    
    def load_from_proguard(self, mapping_file: str):
        """Load mappings from ProGuard mapping.txt format."""
        print(f"Loading ProGuard mappings from {mapping_file}...")
        
        current_class = None
        
        with open(mapping_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # ProGuard format:
                # 'original.class.name' -> 'obfuscated.class.name':
                if ' -> ' in line and line.endswith(':'):
                    parts = line.split(' -> ')
                    if len(parts) == 2:
                        original = parts[0].strip("'")
                        obfuscated = parts[1].strip("' :")
                        self.mappings['classes'][obfuscated] = original
                        current_class = obfuscated
                
                # Method mapping: '    originalMethod(originalDesc) -> obfuscatedMethod'
                elif current_class and ' -> ' in line and '(' in line:
                    # Format: "    methodName(desc) -> obfName"
                    line = line.strip()
                    if ' -> ' in line:
                        parts = line.split(' -> ')
                        if len(parts) == 2:
                            original_part = parts[0]
                            obfuscated = parts[1].strip()
                            
                            # Extract method name from "methodName(desc)"
                            if '(' in original_part:
                                original_method = original_part.split('(')[0]
                                key = f"{current_class}.{obfuscated}"
                                self.mappings['methods'][key] = f"{self.mappings['classes'].get(current_class, current_class)}.{original_method}"
                
                # Field mapping: '    type originalField -> obfuscatedField'
                elif current_class and ' -> ' in line and '(' not in line:
                    line = line.strip()
                    parts = line.split(' -> ')
                    if len(parts) == 2:
                        original_part = parts[0].split()[-1]  # Get field name
                        obfuscated = parts[1].strip()
                        key = f"{current_class}/{obfuscated}"
                        self.mappings['fields'][key] = f"{self.mappings['classes'].get(current_class, current_class)}/{original_part}"
        
        print(f"Loaded {len(self.mappings['classes'])} class mappings from ProGuard file")
        print(f"Loaded {len(self.mappings['methods'])} method mappings")
        print(f"Loaded {len(self.mappings['fields'])} field mappings")
    
    def get_class_mapping(self, obf_name: str) -> Optional[str]:
        """Get MCP name for obfuscated class."""
        return self.mappings['classes'].get(obf_name)
    
    def get_method_mapping(self, class_name: str, method_name: str) -> Optional[str]:
        """Get MCP name for obfuscated method."""
        key = f"{class_name}.{method_name}"
        return self.mappings['methods'].get(key)
    
    def get_field_mapping(self, class_name: str, field_name: str) -> Optional[str]:
        """Get MCP name for obfuscated field."""
        key = f"{class_name}/{field_name}"
        return self.mappings['fields'].get(key)


class ModDeobfuscator:
    """Decompiles and deobfuscates Minecraft mods."""
    
    def __init__(self, jar_path: str, mc_version: str = "1.8.9"):
        self.jar_path = Path(jar_path)
        self.mc_version = mc_version
        self.mappings = MCPMappingLoader(mc_version)
        self.decompiled_dir = None
        self.deobfuscated_dir = None
    
    def decompile(self, decompiler: str = "cfr", decompiler_path: Optional[str] = None, output_dir: Optional[str] = None) -> Path:
        """
        Decompile the JAR file using specified decompiler.
        
        Supported decompilers:
        - cfr: CFR decompiler (recommended)
        - jd-cli: JD-CLI (command-line JD-GUI)
        - fernflower: Fernflower decompiler
        """
        if output_dir is None:
            output_dir = self.jar_path.stem + "_decompiled"
        
        self.decompiled_dir = Path(output_dir)
        self.decompiled_dir.mkdir(exist_ok=True)
        
        print(f"\nDecompiling {self.jar_path.name} using {decompiler}...")
        
        # Determine decompiler path
        if decompiler_path:
            decompiler_jar = Path(decompiler_path)
        else:
            # Try standard locations
            if decompiler == "cfr":
                decompiler_jar = Path("/workspace/tools/cfr.jar")  # Docker path
                if not decompiler_jar.exists():
                    decompiler_jar = Path("tools/cfr.jar")  # Local path
            elif decompiler == "jd-cli":
                decompiler_jar = Path("/workspace/tools/jd-cli.jar")
                if not decompiler_jar.exists():
                    decompiler_jar = Path("tools/jd-cli.jar")
            elif decompiler == "fernflower":
                decompiler_jar = Path("/workspace/tools/fernflower.jar")
                if not decompiler_jar.exists():
                    decompiler_jar = Path("tools/fernflower.jar")
            else:
                print(f"✗ Unknown decompiler: {decompiler}")
                return self.decompiled_dir
        
        if not decompiler_jar.exists():
            print(f"⚠ Warning: Decompiler not found: {decompiler_jar}")
            print(f"Please download {decompiler} and place it in tools/ directory")
            print("Or specify path with --decompiler-path option")
            return self.decompiled_dir
        
        # Build command based on decompiler
        if decompiler == "cfr":
            cmd = [
                "java", "-jar", str(decompiler_jar),
                str(self.jar_path),
                "--outputdir", str(self.decompiled_dir),
                "--caseinsensitivefs", "true"
            ]
        elif decompiler == "jd-cli":
            cmd = [
                "java", "-jar", str(decompiler_jar),
                str(self.jar_path),
                "-od", str(self.decompiled_dir)
            ]
        elif decompiler == "fernflower":
            cmd = [
                "java", "-jar", str(decompiler_jar),
                str(self.jar_path),
                str(self.decompiled_dir)
            ]
        else:
            print(f"✗ Unsupported decompiler: {decompiler}")
            return self.decompiled_dir
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                print(f"✓ Decompiled to {self.decompiled_dir}")
            else:
                print(f"⚠ Decompilation warnings: {result.stderr[:500]}")
                if result.stdout:
                    print(f"Output: {result.stdout[:200]}")
        except subprocess.TimeoutExpired:
            print("⚠ Decompilation timed out")
        except Exception as e:
            print(f"✗ Error during decompilation: {e}")
        
        return self.decompiled_dir
    
    def load_mappings(self, mappings_file: str):
        """Load MCP mappings from file."""
        mappings_path = Path(mappings_file)
        
        if not mappings_path.exists():
            print(f"⚠ Mappings file not found: {mappings_file}")
            print("\nTo get mappings:")
            print("1. Download from MCPBot: http://export.mcpbot.bspk.rs/")
            print("2. Or use Forge's mapping files")
            print("3. Or extract from MCP/Forge installation")
            print("4. Or use ProGuard mapping.txt if available")
            return False
        
        if mappings_file.endswith('.srg'):
            self.mappings.load_from_srg(mappings_file)
        elif mappings_file.endswith('.csv'):
            self.mappings.load_from_csv(mappings_file)
        elif mappings_file.endswith('.txt') or 'mapping' in mappings_file.lower():
            # Try ProGuard mapping format
            self.mappings.load_from_proguard(mappings_file)
        else:
            print(f"⚠ Unknown mappings format: {mappings_file}")
            print("Trying to load as SRG format...")
            try:
                self.mappings.load_from_srg(mappings_file)
            except:
                return False
        
        return True
    
    def apply_mappings_with_specialsource(self, mappings_file: str, output_jar: Optional[str] = None) -> Optional[Path]:
        """
        Apply mappings using SpecialSource tool (more accurate than text replacement).
        This remaps the JAR file before decompilation.
        """
        if output_jar is None:
            output_jar = self.jar_path.stem + "_remapped.jar"
        
        output_path = Path(output_jar)
        
        # Find SpecialSource
        specialsource_jar = Path("/workspace/tools/specialsource.jar")
        if not specialsource_jar.exists():
            specialsource_jar = Path("tools/specialsource.jar")
        
        if not specialsource_jar.exists():
            print("⚠ SpecialSource not found. Using text-based mapping instead.")
            return None
        
        print(f"\nApplying mappings with SpecialSource...")
        
        cmd = [
            "java", "-jar", str(specialsource_jar),
            "--in-jar", str(self.jar_path),
            "--out-jar", str(output_path),
            "--mappings", mappings_file,
            "--live"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                print(f"✓ Remapped JAR saved to {output_path}")
                return output_path
            else:
                print(f"⚠ SpecialSource warnings: {result.stderr[:500]}")
                return None
        except Exception as e:
            print(f"✗ Error applying mappings: {e}")
            return None
    
    def apply_mappings_to_java(self, java_file: Path, output_file: Path):
        """Apply MCP mappings to a decompiled Java file."""
        content = java_file.read_text(encoding='utf-8', errors='ignore')
        original_content = content
        
        # Apply class name mappings
        # Match class references: "class a", "extends a", "implements a", "new a()", "a.method()"
        for obf, mapped in self.mappings.mappings['classes'].items():
            # Get just the class name (last part after package)
            mapped_class_name = mapped.split('.')[-1] if '.' in mapped else mapped
            
            # Replace class declarations
            content = re.sub(
                rf'\bclass\s+{re.escape(obf)}\b',
                f'class {mapped_class_name}',
                content
            )
            
            # Replace extends/implements
            content = re.sub(
                rf'\bextends\s+{re.escape(obf)}\b',
                f'extends {mapped_class_name}',
                content
            )
            content = re.sub(
                rf'\bimplements\s+{re.escape(obf)}\b',
                f'implements {mapped_class_name}',
                content
            )
            
            # Replace variable/field types
            content = re.sub(
                rf'\b{re.escape(obf)}\s+(\w+)',
                f'{mapped_class_name} \\1',
                content
            )
            
            # Replace new instances
            content = re.sub(
                rf'\bnew\s+{re.escape(obf)}\s*\(',
                f'new {mapped_class_name}(',
                content
            )
        
        # Apply method mappings (simplified - full implementation is complex)
        for obf_key, mapped_key in self.mappings.mappings['methods'].items():
            obf_class, obf_method = obf_key.split('.', 1)
            mapped_class, mapped_method = mapped_key.split('.', 1)
            
            # Replace method calls: obf_class.obf_method( or obf_method(
            if obf_method in content:
                # Simple replacement (may have false positives)
                content = re.sub(
                    rf'\b{re.escape(obf_method)}\s*\(',
                    f'{mapped_method}(',
                    content
                )
        
        # Write deobfuscated file
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(content, encoding='utf-8')
        
        return content != original_content
    
    def deobfuscate(self, mappings_file: str, output_dir: Optional[str] = None) -> Path:
        """Deobfuscate decompiled code using mappings."""
        if self.decompiled_dir is None:
            print("⚠ Must decompile first!")
            return None
        
        if not self.load_mappings(mappings_file):
            return None
        
        if output_dir is None:
            output_dir = self.jar_path.stem + "_deobfuscated"
        
        self.deobfuscated_dir = Path(output_dir)
        self.deobfuscated_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\nDeobfuscating code...")
        
        java_files = list(self.decompiled_dir.rglob("*.java"))
        deobfuscated_count = 0
        
        for java_file in java_files:
            # Calculate relative path
            rel_path = java_file.relative_to(self.decompiled_dir)
            output_file = self.deobfuscated_dir / rel_path
            
            if self.apply_mappings_to_java(java_file, output_file):
                deobfuscated_count += 1
        
        print(f"✓ Deobfuscated {deobfuscated_count} files")
        print(f"✓ Output: {self.deobfuscated_dir}")
        
        return self.deobfuscated_dir
    
    def analyze_deobfuscated(self):
        """Analyze deobfuscated code for interesting patterns."""
        if self.deobfuscated_dir is None:
            print("⚠ Must deobfuscate first!")
            return
        
        print("\nAnalyzing deobfuscated code...")
        
        java_files = list(self.deobfuscated_dir.rglob("*.java"))
        
        findings = {
            'webhook_references': [],
            'token_access': [],
            'network_code': [],
            'session_access': [],
            'discord_references': []
        }
        
        patterns = {
            'webhook_references': [
                r'webhook',
                r'discord\.com/api/webhooks',
                r'https?://.*webhook'
            ],
            'token_access': [
                r'\.getToken\(\)',
                r'\.getSession\(\)',
                r'accessToken',
                r'sessionToken'
            ],
            'network_code': [
                r'HttpURLConnection',
                r'URLConnection',
                r'\.openConnection\(\)',
                r'URL\(.*http'
            ],
            'session_access': [
                r'Minecraft\.getMinecraft\(\)\.getSession\(\)',
                r'Session\.class',
                r'net\.minecraft\.util\.Session'
            ],
            'discord_references': [
                r'discord',
                r'Discord'
            ]
        }
        
        for java_file in java_files:
            try:
                content = java_file.read_text(encoding='utf-8', errors='ignore')
                
                for category, pattern_list in patterns.items():
                    for pattern in pattern_list:
                        if re.search(pattern, content, re.IGNORECASE):
                            findings[category].append({
                                'file': str(java_file.relative_to(self.deobfuscated_dir)),
                                'pattern': pattern
                            })
                            break  # Only report once per file per category
            except Exception as e:
                continue
        
        # Print findings
        print("\n" + "=" * 60)
        print("ANALYSIS RESULTS")
        print("=" * 60)
        
        for category, items in findings.items():
            if items:
                print(f"\n{category.replace('_', ' ').title()}:")
                for item in items[:5]:  # Show first 5
                    print(f"  ⚠ {item['file']}")
        
        return findings


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python mod_deobfuscator.py <mod.jar> [mappings.srg] [options]")
        print("\nOptions:")
        print("  --decompiler <name>    Decompiler to use: cfr, jd-cli, fernflower (default: cfr)")
        print("  --decompiler-path <p>  Path to decompiler JAR (auto-detected if not specified)")
        print("  --mc-version <ver>     Minecraft version (default: 1.8.9)")
        print("  --output <dir>         Output directory")
        print("  --analyze              Analyze deobfuscated code")
        print("  --use-specialsource    Use SpecialSource for mapping (recommended)")
        print("\nExample:")
        print("  python mod_deobfuscator.py mod.jar mappings.srg --analyze")
        sys.exit(1)
    
    jar_path = sys.argv[1]
    # Only treat arg2 as mappings file if it doesn't start with --
    mappings_file = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else None
    
    # Parse options
    decompiler = "cfr"
    decompiler_path = None
    mc_version = "1.8.9"
    output_dir = None
    analyze = False
    use_specialsource = True
    
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == '--decompiler' and i + 1 < len(sys.argv):
            decompiler = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--decompiler-path' and i + 1 < len(sys.argv):
            decompiler_path = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--mc-version' and i + 1 < len(sys.argv):
            mc_version = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--output' and i + 1 < len(sys.argv):
            output_dir = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--analyze':
            analyze = True
            i += 1
        elif sys.argv[i] == '--use-specialsource':
            use_specialsource = True
            i += 1
        elif sys.argv[i] == '--no-specialsource':
            use_specialsource = False
            i += 1
        else:
            i += 1
    
    try:
        deobfuscator = ModDeobfuscator(jar_path, mc_version)
        
        # Apply mappings with SpecialSource first (if mappings provided and enabled)
        remapped_jar = None
        if mappings_file and use_specialsource:
            remapped_jar = deobfuscator.apply_mappings_with_specialsource(mappings_file)
        
        # Use remapped JAR if available, otherwise original
        jar_to_decompile = remapped_jar if remapped_jar else deobfuscator.jar_path
        if remapped_jar:
            # Create new deobfuscator for remapped JAR
            deobfuscator = ModDeobfuscator(jar_to_decompile, mc_version)
        
        # Decompile
        deobfuscator.decompile(decompiler, decompiler_path, output_dir)
        
        # Apply text-based mappings to decompiled code (for additional cleanup)
        if mappings_file:
            deobfuscator.deobfuscate(mappings_file, output_dir)
            
            if analyze:
                deobfuscator.analyze_deobfuscated()
        else:
            print("\n⚠ No mappings file provided. Code is decompiled but not deobfuscated.")
            print("To deobfuscate, provide a mappings file:")
            print("  python mod_deobfuscator.py mod.jar mappings.srg")
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

