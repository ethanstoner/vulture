#!/usr/bin/env python3
"""
Minecraft Forge Mod Analyzer
Vulture - Educational tool for analyzing Minecraft mod JAR files

This tool analyzes mod structure, classes, and dependencies.
It does NOT modify mods - only reads and reports information.
"""

import zipfile
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set
import re


class ModAnalyzer:
    """Analyzes Minecraft Forge mod JAR files."""
    
    def __init__(self, jar_path: str):
        self.jar_path = Path(jar_path)
        if not self.jar_path.exists():
            raise FileNotFoundError(f"JAR file not found: {jar_path}")
        
        self.jar = zipfile.ZipFile(self.jar_path, 'r')
        self.classes: List[str] = []
        self.resources: List[str] = []
        self.mod_info: Optional[Dict] = None
        
    def analyze(self) -> Dict:
        """Perform complete analysis of the mod."""
        print(f"Analyzing mod: {self.jar_path.name}")
        print("=" * 60)
        
        # Extract file list
        self._extract_file_list()
        
        # Find mod metadata
        self._find_mod_metadata()
        
        # Analyze classes
        class_analysis = self._analyze_classes()
        
        # Check for suspicious patterns
        security_analysis = self._security_analysis()
        
        return {
            'mod_name': self.jar_path.name,
            'file_count': len(self.jar.namelist()),
            'classes': class_analysis,
            'mod_info': self.mod_info,
            'security_flags': security_analysis,
            'resources': self.resources[:20]  # First 20 resources
        }
    
    def _extract_file_list(self):
        """Extract list of all files in the JAR."""
        all_files = self.jar.namelist()
        
        for file_path in all_files:
            if file_path.endswith('.class'):
                self.classes.append(file_path)
            elif not file_path.endswith('/'):
                self.resources.append(file_path)
        
        print(f"Total files: {len(all_files)}")
        print(f"Class files: {len(self.classes)}")
        print(f"Resource files: {len(self.resources)}")
    
    def _find_mod_metadata(self):
        """Find mod metadata files."""
        # Check for mcmod.info
        if 'mcmod.info' in self.jar.namelist():
            try:
                info_content = self.jar.read('mcmod.info').decode('utf-8')
                # Try to parse as JSON
                try:
                    self.mod_info = json.loads(info_content)
                except:
                    # Might be in old format, try to extract info
                    self.mod_info = {'raw': info_content}
                print("\n✓ Found mcmod.info")
            except Exception as e:
                print(f"\n✗ Error reading mcmod.info: {e}")
        
        # Check for META-INF
        meta_files = [f for f in self.jar.namelist() if f.startswith('META-INF/')]
        if meta_files:
            print(f"✓ Found {len(meta_files)} META-INF files")
    
    def _analyze_classes(self) -> Dict:
        """Analyze class files for interesting patterns."""
        print("\nAnalyzing classes...")
        
        class_analysis = {
            'total': len(self.classes),
            'gui_classes': [],
            'session_classes': [],
            'network_classes': [],
            'data_classes': [],
            'main_classes': []
        }
        
        # Patterns to look for
        gui_pattern = re.compile(r'.*[Gg]ui.*|.*[Ss]creen.*|.*[Bb]utton.*')
        session_pattern = re.compile(r'.*[Ss]ession.*|.*[Aa]uth.*|.*[Tt]oken.*')
        network_pattern = re.compile(r'.*[Nn]et.*|.*[Hh]ttp.*|.*[Ww]ebhook.*|.*[Uu]rl.*')
        data_pattern = re.compile(r'.*[Dd]ata.*|.*[Jj]son.*|.*[Cc]onfig.*')
        main_pattern = re.compile(r'.*[Mm]od.*|.*[Mm]ain.*')
        
        for class_path in self.classes:
            class_name = class_path.replace('/', '.').replace('.class', '')
            
            if gui_pattern.search(class_name):
                class_analysis['gui_classes'].append(class_name)
            if session_pattern.search(class_name):
                class_analysis['session_classes'].append(class_name)
            if network_pattern.search(class_name):
                class_analysis['network_classes'].append(class_name)
            if data_pattern.search(class_name):
                class_analysis['data_classes'].append(class_name)
            if main_pattern.search(class_name):
                class_analysis['main_classes'].append(class_name)
        
        return class_analysis
    
    def _security_analysis(self) -> Dict:
        """Analyze for potentially suspicious patterns."""
        print("\nPerforming security analysis...")
        
        flags = {
            'has_network_classes': False,
            'has_http_requests': False,
            'has_webhook_references': False,
            'has_token_access': False,
            'has_reflection': False,
            'suspicious_patterns': []
        }
        
        # Check class names
        all_class_names = ' '.join(self.classes)
        
        # Network patterns
        if re.search(r'[Hh]ttp|URL|Webhook|Network|Socket', all_class_names):
            flags['has_network_classes'] = True
            flags['suspicious_patterns'].append('Network-related classes found')
        
        # Webhook patterns
        if re.search(r'[Ww]ebhook|[Dd]iscord', all_class_names):
            flags['has_webhook_references'] = True
            flags['suspicious_patterns'].append('Webhook references found')
        
        # Token patterns
        if re.search(r'[Tt]oken|[Ss]ession', all_class_names):
            flags['has_token_access'] = True
            flags['suspicious_patterns'].append('Token/session access classes found')
        
        # Reflection patterns
        if re.search(r'[Rr]eflect|[Ff]ield|[Mm]ethod', all_class_names):
            flags['has_reflection'] = True
            flags['suspicious_patterns'].append('Reflection usage detected')
        
        # Check resource files for URLs
        for resource in self.resources:
            if resource.endswith('.json') or resource.endswith('.txt'):
                try:
                    content = self.jar.read(resource).decode('utf-8', errors='ignore')
                    if re.search(r'https?://', content):
                        flags['has_http_requests'] = True
                        flags['suspicious_patterns'].append(f'URL found in {resource}')
                except:
                    pass
        
        return flags
    
    def print_report(self, analysis: Dict):
        """Print a formatted analysis report."""
        print("\n" + "=" * 60)
        print("MOD ANALYSIS REPORT")
        print("=" * 60)
        
        print(f"\nMod File: {analysis['mod_name']}")
        print(f"Total Files: {analysis['file_count']}")
        
        if analysis['mod_info']:
            print("\nMod Information:")
            if isinstance(analysis['mod_info'], dict) and 'raw' not in analysis['mod_info']:
                for key, value in analysis['mod_info'].items():
                    print(f"  {key}: {value}")
            else:
                print(f"  {analysis['mod_info']}")
        
        print("\nClass Analysis:")
        classes = analysis['classes']
        print(f"  Total Classes: {classes['total']}")
        print(f"  GUI Classes: {len(classes['gui_classes'])}")
        if classes['gui_classes']:
            for cls in classes['gui_classes'][:5]:
                print(f"    - {cls}")
        print(f"  Session/Auth Classes: {len(classes['session_classes'])}")
        if classes['session_classes']:
            for cls in classes['session_classes'][:5]:
                print(f"    - {cls}")
        print(f"  Network Classes: {len(classes['network_classes'])}")
        if classes['network_classes']:
            for cls in classes['network_classes'][:5]:
                print(f"    - {cls}")
        print(f"  Data Classes: {len(classes['data_classes'])}")
        if classes['data_classes']:
            for cls in classes['data_classes'][:5]:
                print(f"    - {cls}")
        
        print("\nSecurity Analysis:")
        flags = analysis['security_flags']
        print(f"  Network Classes: {'✓' if flags['has_network_classes'] else '✗'}")
        print(f"  HTTP Requests: {'✓' if flags['has_http_requests'] else '✗'}")
        print(f"  Webhook References: {'✓' if flags['has_webhook_references'] else '✗'}")
        print(f"  Token Access: {'✓' if flags['has_token_access'] else '✗'}")
        print(f"  Reflection Usage: {'✓' if flags['has_reflection'] else '✗'}")
        
        if flags['suspicious_patterns']:
            print("\n  Suspicious Patterns Detected:")
            for pattern in flags['suspicious_patterns']:
                print(f"    ⚠ {pattern}")
        
        print("\n" + "=" * 60)
    
    def close(self):
        """Close the JAR file."""
        self.jar.close()


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python mod_analyzer.py <path_to_mod.jar>")
        print("\nExample:")
        print("  python mod_analyzer.py account-manager-1.8.9.jar")
        sys.exit(1)
    
    jar_path = sys.argv[1]
    
    try:
        analyzer = ModAnalyzer(jar_path)
        analysis = analyzer.analyze()
        analyzer.print_report(analysis)
        analyzer.close()
        
        # Optionally save to JSON
        if len(sys.argv) > 2 and sys.argv[2] == '--json':
            output_file = Path(jar_path).stem + '_analysis.json'
            with open(output_file, 'w') as f:
                json.dump(analysis, f, indent=2)
            print(f"\nAnalysis saved to: {output_file}")
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

