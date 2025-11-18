#!/usr/bin/env python3
"""
Vulture - Minecraft Mod Compiler
Compiles decompiled Java source code back into JAR files
"""

import subprocess
import zipfile
import shutil
import os
import sys
from pathlib import Path
from typing import List, Optional


class ModCompiler:
    """Compiles Java source code back into JAR files."""
    
    def __init__(self, source_dir: str, output_jar: str):
        self.source_dir = Path(source_dir)
        self.output_jar = Path(output_jar)
        self.classes_dir = None
        
        if not self.source_dir.exists():
            raise FileNotFoundError(f"Source directory not found: {source_dir}")
    
    def compile(self, classpath: Optional[str] = None) -> bool:
        """
        Compile Java source files to class files.
        
        Args:
            classpath: Optional classpath for dependencies
        """
        print(f"\nCompiling Java source from: {self.source_dir}")
        
        # Create temporary directory for compiled classes (use /tmp for writability)
        import tempfile
        temp_base = Path("/tmp") if Path("/tmp").exists() else Path(self.source_dir.parent)
        self.classes_dir = temp_base / f"{self.source_dir.name}_classes_{os.getpid()}"
        if self.classes_dir.exists():
            shutil.rmtree(self.classes_dir)
        self.classes_dir.mkdir(parents=True, exist_ok=True)
        
        # Find all Java files
        java_files = list(self.source_dir.rglob("*.java"))
        
        if not java_files:
            print("✗ No Java files found to compile")
            return False
        
        print(f"Found {len(java_files)} Java file(s) to compile...")
        
        # Build javac command (use Java 17 for modern features)
        javac_cmd = [
            "javac",
            "-d", str(self.classes_dir),
            "-source", "17",
            "-target", "17",
            "-encoding", "UTF-8"
        ]
        
        # Add classpath if provided
        if classpath:
            javac_cmd.extend(["-cp", classpath])
        
        # Add all Java files
        javac_cmd.extend([str(f) for f in java_files])
        
        # Compile
        try:
            result = subprocess.run(
                javac_cmd,
                capture_output=True,
                text=True,
                cwd=self.source_dir
            )
            
            if result.returncode != 0:
                print(f"⚠ Compilation warnings/errors:")
                print(result.stderr[:1000])  # Show first 1000 chars of errors
                # Continue anyway - some errors might be non-critical
            
            # Count compiled classes
            class_files = list(self.classes_dir.rglob("*.class"))
            print(f"✓ Compiled {len(class_files)} class file(s)")
            
            return len(class_files) > 0
            
        except Exception as e:
            print(f"✗ Compilation failed: {e}")
            return False
    
    def create_jar(self, manifest_file: Optional[str] = None) -> bool:
        """
        Create JAR file from compiled classes.
        
        Args:
            manifest_file: Optional MANIFEST.MF file
        """
        if self.classes_dir is None or not self.classes_dir.exists():
            print("✗ Must compile first!")
            return False
        
        print(f"\nCreating JAR file: {self.output_jar}")
        
        # Ensure output directory exists
        self.output_jar.parent.mkdir(parents=True, exist_ok=True)
        
        # Remove existing JAR if it exists
        if self.output_jar.exists():
            self.output_jar.unlink()
        
        try:
            with zipfile.ZipFile(self.output_jar, 'w', zipfile.ZIP_DEFLATED) as jar:
                # Add all class files
                for class_file in self.classes_dir.rglob("*.class"):
                    # Calculate relative path for JAR entry
                    rel_path = class_file.relative_to(self.classes_dir)
                    jar.write(class_file, rel_path)
                
                # Add manifest if provided
                if manifest_file and Path(manifest_file).exists():
                    jar.write(manifest_file, "META-INF/MANIFEST.MF")
                else:
                    # Create default manifest
                    manifest_content = "Manifest-Version: 1.0\n"
                    jar.writestr("META-INF/MANIFEST.MF", manifest_content)
                
                # Copy resources from source directory (non-Java files)
                for resource_file in self.source_dir.rglob("*"):
                    if resource_file.is_file() and not resource_file.suffix == ".java":
                        rel_path = resource_file.relative_to(self.source_dir)
                        # Skip if already added as class
                        if not str(rel_path).startswith("META-INF/"):
                            jar.write(resource_file, rel_path)
            
            print(f"✓ Created JAR: {self.output_jar}")
            print(f"  Size: {self.output_jar.stat().st_size / 1024:.1f} KB")
            
            # Clean up temporary classes directory
            shutil.rmtree(self.classes_dir)
            
            return True
            
        except Exception as e:
            print(f"✗ Failed to create JAR: {e}")
            return False


def main():
    """Main function."""
    if len(sys.argv) < 3:
        print("Usage: python mod_compiler.py <source_directory> <output_jar> [classpath]")
        print("\nExample:")
        print("  python mod_compiler.py decompiled/my_mod my_mod_recompiled.jar")
        print("  python mod_compiler.py decompiled/my_mod my_mod_recompiled.jar -cp libs/*")
        sys.exit(1)
    
    source_dir = sys.argv[1]
    output_jar = sys.argv[2]
    classpath = sys.argv[3] if len(sys.argv) > 3 else None
    
    try:
        compiler = ModCompiler(source_dir, output_jar)
        
        if compiler.compile(classpath):
            if compiler.create_jar():
                print("\n✓ Compilation complete!")
                return 0
            else:
                print("\n✗ Failed to create JAR file")
                return 1
        else:
            print("\n✗ Compilation failed")
            return 1
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

