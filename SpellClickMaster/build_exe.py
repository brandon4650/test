"""
Build script to create a standalone executable for the Spell Caster application.
"""
import os
import sys
import shutil
import zipfile
import datetime
import PyInstaller.__main__

print("====================================")
print("Spell Caster - Build Script")
print("====================================")
print(f"Current directory: {os.getcwd()}")
print(f"Python version: {sys.version}")
print("Creating standalone executable package...")

# Create build directories
build_dir = os.path.join(os.getcwd(), 'build')
dist_dir = os.path.join(os.getcwd(), 'dist')
package_dir = os.path.join(dist_dir, 'SpellCaster')

# Clean previous build if needed
if os.path.exists(package_dir):
    print(f"Cleaning previous build directory: {package_dir}")
    shutil.rmtree(package_dir)

# Create necessary directories
os.makedirs(dist_dir, exist_ok=True)
os.makedirs(package_dir, exist_ok=True)
os.makedirs('assets', exist_ok=True)

# Create a default app icon if it doesn't exist
if not os.path.exists('assets/app_icon.ico'):
    print("Creating app icon...")
    # If .ico not available, copy the .svg file
    if os.path.exists('assets/app_icon.svg'):
        shutil.copy('assets/app_icon.svg', 'assets/app_icon.svg.bak')
    
    # Create a simple icon file (this is a placeholder)
    with open('assets/app_icon.ico', 'wb') as f:
        # Minimal valid .ico file content
        f.write(b'\x00\x00\x01\x00\x01\x00\x10\x10\x00\x00\x01\x00\x04\x00\x28\x01\x00\x00\x16\x00\x00\x00\x28\x00\x00\x00\x10\x00\x00\x00\x20\x00\x00\x00\x01\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')

# Copy documentation to package directory
if os.path.exists('README.md'):
    print("Copying README.md to package...")
    shutil.copy('README.md', os.path.join(package_dir, 'README.md'))
    
if os.path.exists('INSTALLATION_GUIDE.md'):
    print("Copying INSTALLATION_GUIDE.md to package...")
    shutil.copy('INSTALLATION_GUIDE.md', os.path.join(package_dir, 'INSTALLATION_GUIDE.md'))

# Define PyInstaller arguments
pyinstaller_args = [
    'main.py',                                    # Main script
    '--name=SpellCaster',                         # Output name
    '--onefile',                                  # Create a single executable
    '--windowed',                                 # Windows mode (no console)
    '--icon=assets/app_icon.ico',                 # Icon
    f'--distpath={package_dir}',                  # Output directory
    '--add-data=assets:assets',                   # Include assets folder
    '--hidden-import=PyQt5.sip',                  # Required hidden imports
    '--hidden-import=cv2',
    '--hidden-import=numpy',
    '--hidden-import=pyautogui',
    '--hidden-import=PIL.Image',
    '--hidden-import=PyQt5.QtCore',
    '--hidden-import=PyQt5.QtGui',
    '--hidden-import=PyQt5.QtWidgets',
    '--log-level=INFO',                           # Logging level
    '--clean',                                    # Clean cache
    '--uac-admin',                                # Request admin rights (for keyboard control)
    '--version-file=version_info.txt',            # Version info
]

# Create version info file
with open('version_info.txt', 'w') as f:
    f.write(f"""
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Spell Caster'),
        StringStruct(u'FileDescription', u'Spell Caster - Automatic Spell Detection'),
        StringStruct(u'FileVersion', u'1.0.0'),
        StringStruct(u'InternalName', u'spellcaster'),
        StringStruct(u'LegalCopyright', u'Copyright (c) {datetime.datetime.now().year}'),
        StringStruct(u'OriginalFilename', u'SpellCaster.exe'),
        StringStruct(u'ProductName', u'Spell Caster'),
        StringStruct(u'ProductVersion', u'1.0.0')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
""")

# Create a sample configuration file
sample_config_path = os.path.join(package_dir, 'sample_config.json')
with open(sample_config_path, 'w') as f:
    f.write("""
{
  "scan_area": [100, 100, 300, 100],
  "detection_frequency": 0.1,
  "confidence_threshold": 0.8,
  "cooldown": 0.5,
  "autostart": false,
  "minimize_to_tray": true,
  "game_type": "World of Warcraft",
  "game_resolution": "1920x1080",
  "keybinds": {
    "N5": "1",
    "C1": "2",
    "N1": "3"
  }
}
""")

# Create a templates directory
templates_dir = os.path.join(package_dir, 'templates')
os.makedirs(templates_dir, exist_ok=True)

# Run PyInstaller
print("\nBuilding SpellCaster executable with PyInstaller...")
try:
    PyInstaller.__main__.run(pyinstaller_args)
    print("PyInstaller completed successfully!")
except Exception as e:
    print(f"Error building executable: {str(e)}")
    sys.exit(1)

# Create ZIP package
zip_filename = os.path.join(dist_dir, f"SpellCaster_v1.0.0.zip")
try:
    print("\nCreating ZIP package...")
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, package_dir)
                zipf.write(file_path, arcname)
    print(f"ZIP package created at: {zip_filename}")
except Exception as e:
    print(f"Error creating ZIP package: {str(e)}")

# Final message
print("\n====================================")
print("Build completed successfully!")
print("====================================")
print(f"Executable: {os.path.join(package_dir, 'SpellCaster.exe')}")
print(f"ZIP Package: {zip_filename}")
print("\nInstructions:")
print("1. Extract the ZIP file to a location of your choice")
print("2. Run SpellCaster.exe to start the application")
print("3. Follow the setup wizard to configure the application")
print("====================================")