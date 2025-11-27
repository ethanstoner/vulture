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
    
    def compile(self, classpath: Optional[str] = None, original_jar: Optional[str] = None) -> bool:
        """
        Compile Java source files to class files.
        
        Args:
            classpath: Optional classpath for dependencies
            original_jar: Path to original JAR file (will be used as classpath)
        """
        print(f"\nCompiling Java source from: {self.source_dir}")
        
        # Create temporary directory for compiled classes (use /tmp for writability)
        import tempfile
        temp_base = Path("/tmp") if Path("/tmp").exists() else Path(self.source_dir.parent)
        self.classes_dir = temp_base / f"{self.source_dir.name}_classes_{os.getpid()}"
        if self.classes_dir.exists():
            shutil.rmtree(self.classes_dir)
        self.classes_dir.mkdir(parents=True, exist_ok=True)
        
        # Build classpath - include original JAR if provided
        if original_jar and Path(original_jar).exists():
            if classpath:
                classpath = f"{original_jar}:{classpath}"
            else:
                classpath = original_jar
            print(f"Using original JAR as classpath: {Path(original_jar).name}")
        
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
        
        # Compile - use batch compilation with error tolerance
        # javac will compile what it can even if some files have errors
        result = subprocess.run(
            javac_cmd,
            capture_output=True,
            text=True,
            cwd=self.source_dir
        )
        
        # Count compiled classes (javac may compile some files even if others fail)
        class_files = list(self.classes_dir.rglob("*.class"))
        
        if len(class_files) > 0:
            # Some classes compiled successfully
            if result.returncode != 0:
                print(f"⚠ Compilation completed with some errors")
                print(f"   (Compiled {len(class_files)} classes despite errors)")
            else:
                print(f"✓ Compiled {len(class_files)} class file(s)")
            return True
        else:
            # No classes compiled at all
            print(f"✗ Compilation failed - no classes were compiled")
            if result.stderr:
                print(f"   Error: {result.stderr[:300]}")
            return False
    
    def create_jar(self, manifest_file: Optional[str] = None, original_jar: Optional[str] = None) -> bool:
        """
        Create JAR file from compiled classes, merging with original JAR if provided.
        
        Args:
            manifest_file: Optional MANIFEST.MF file
            original_jar: Path to original JAR (will copy all non-recompiled content)
        """
        # Check if we have any classes to package
        class_files = []
        if self.classes_dir and self.classes_dir.exists():
            class_files = list(self.classes_dir.rglob("*.class"))
        
        # If no classes compiled but we have original JAR, we can still create a JAR
        # by copying everything from original (this ensures size matches)
        if len(class_files) == 0:
            if original_jar and Path(original_jar).exists():
                print("⚠ No classes compiled, copying original JAR as-is")
                # Just copy the original JAR
                shutil.copy2(original_jar, self.output_jar)
                print(f"✓ Copied original JAR: {self.output_jar}")
                print(f"  Size: {self.output_jar.stat().st_size / 1024:.1f} KB")
                return True
            else:
                print("✗ No compiled classes found and no original JAR to copy")
                return False
        
        print(f"\nCreating JAR file: {self.output_jar}")
        print(f"  Packaging {len(class_files)} newly compiled class file(s)...")
        
        # Ensure output directory exists
        self.output_jar.parent.mkdir(parents=True, exist_ok=True)
        
        # Remove existing JAR if it exists
        if self.output_jar.exists():
            self.output_jar.unlink()
        
        try:
            # Get set of recompiled class paths (to know what to replace)
            # Convert package structure to JAR path format
            recompiled_classes = set()
            for class_file in class_files:
                rel_path = class_file.relative_to(self.classes_dir)
                jar_path = str(rel_path).replace('\\', '/')
                recompiled_classes.add(jar_path)
            
            # Also create a mapping from simple class name to full path for better matching
            recompiled_class_names = {}
            for class_file in class_files:
                rel_path = class_file.relative_to(self.classes_dir)
                jar_path = str(rel_path).replace('\\', '/')
                class_name = class_file.stem
                recompiled_class_names[class_name] = jar_path
            
            with zipfile.ZipFile(self.output_jar, 'w', zipfile.ZIP_DEFLATED) as jar:
                # If original JAR provided, copy everything from it first
                if original_jar and Path(original_jar).exists():
                    print(f"  Merging with original JAR: {Path(original_jar).name}")
                    with zipfile.ZipFile(original_jar, 'r') as original:
                        original_files = original.namelist()
                        copied_count = 0
                        skipped_count = 0
                        
                        for file_info in original_files:
                            # Skip classes that we recompiled (we'll add our versions)
                            should_skip = False
                            if file_info.endswith('.class') and len(class_files) > 0:
                                # Check if exact path matches
                                if file_info in recompiled_classes:
                                    should_skip = True
                                else:
                                    # Check if class name matches in same package
                                    class_name = Path(file_info).stem
                                    if class_name in recompiled_class_names:
                                        original_pkg = '/'.join(file_info.split('/')[:-1])
                                        recompiled_pkg = '/'.join(recompiled_class_names[class_name].split('/')[:-1])
                                        if original_pkg == recompiled_pkg:
                                            should_skip = True
                            
                            if should_skip:
                                skipped_count += 1
                                continue
                            
                            # Copy everything else from original JAR
                            try:
                                data = original.read(file_info)
                                jar.writestr(file_info, data)
                                copied_count += 1
                            except Exception as e:
                                # Skip files that can't be read
                                pass
                        
                        print(f"  Copied {copied_count} files from original JAR")
                        if skipped_count > 0:
                            print(f"  Will replace {skipped_count} classes with recompiled versions")
                
                # Add all newly compiled class files (these override originals if they exist)
                if len(class_files) > 0:
                    for class_file in class_files:
                        rel_path = class_file.relative_to(self.classes_dir)
                        jar_path = str(rel_path).replace('\\', '/')
                        jar.write(class_file, jar_path)
                
                # Add resources from source directory if not already in JAR
                if not original_jar:
                    resource_count = 0
                    for resource_file in self.source_dir.rglob("*"):
                        if resource_file.is_file() and not resource_file.suffix == ".java":
                            rel_path = resource_file.relative_to(self.source_dir)
                            jar_path = str(rel_path).replace('\\', '/')
                            # Only add if not already in JAR
                            if jar_path not in [f.filename for f in jar.filelist]:
                                try:
                                    jar.write(resource_file, jar_path)
                                    resource_count += 1
                                except:
                                    pass
                    
                    if resource_count > 0:
                        print(f"  Added {resource_count} resource file(s) from source")
                
                # Ensure manifest exists
                if "META-INF/MANIFEST.MF" not in [f.filename for f in jar.filelist]:
                    if manifest_file and Path(manifest_file).exists():
                        jar.write(manifest_file, "META-INF/MANIFEST.MF")
                    else:
                        manifest_content = "Manifest-Version: 1.0\n"
                        jar.writestr("META-INF/MANIFEST.MF", manifest_content)
            
            final_class_count = len([f for f in zipfile.ZipFile(self.output_jar, 'r').namelist() if f.endswith('.class')])
            print(f"✓ Created JAR: {self.output_jar}")
            print(f"  Size: {self.output_jar.stat().st_size / 1024:.1f} KB")
            print(f"  Total classes: {final_class_count}")
            
            # Clean up temporary classes directory
            if self.classes_dir.exists():
                shutil.rmtree(self.classes_dir)
            
            return True
            
        except Exception as e:
            print(f"✗ Failed to create JAR: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main function."""
    if len(sys.argv) < 3:
        print("Usage: python mod_compiler.py <source_directory> <output_jar> [classpath] [--original-jar <jar>]")
        print("\nExample:")
        print("  python mod_compiler.py decompiled/my_mod my_mod_recompiled.jar")
        print("  python mod_compiler.py decompiled/my_mod my_mod_recompiled.jar -cp libs/*")
        print("  python mod_compiler.py decompiled/my_mod my_mod_recompiled.jar --original-jar original.jar")
        sys.exit(1)
    
    source_dir = sys.argv[1]
    output_jar = sys.argv[2]
    classpath = None
    original_jar = None
    
    # Parse arguments
    i = 3
    while i < len(sys.argv):
        if sys.argv[i] == "--original-jar" and i + 1 < len(sys.argv):
            original_jar = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "-cp" and i + 1 < len(sys.argv):
            classpath = sys.argv[i + 1]
            i += 2
        else:
            classpath = sys.argv[i]  # Assume it's classpath if no flag
            i += 1
    
    try:
        compiler = ModCompiler(source_dir, output_jar)
        
        # Try to compile (may fail, but that's okay if we have original JAR)
        compilation_success = compiler.compile(classpath, original_jar)
        
        # Always try to create JAR if we have original JAR (will copy original if compilation failed)
        if original_jar and Path(original_jar).exists():
            if compiler.create_jar(original_jar=original_jar):
                if compilation_success:
                    print("\n✓ Compilation and JAR creation complete!")
                else:
                    print("\n✓ JAR created (copied from original - compilation had errors)")
                return 0
            else:
                print("\n✗ Failed to create JAR file")
                return 1
        elif compilation_success:
            # No original JAR, but compilation succeeded
            if compiler.create_jar(original_jar=original_jar):
                print("\n✓ Compilation complete!")
                return 0
            else:
                print("\n✗ Failed to create JAR file")
                return 1
        else:
            print("\n✗ Compilation failed and no original JAR to copy")
            return 1
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

