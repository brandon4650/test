# Spell Caster - Installation Guide

This guide will help you install and run the Spell Caster application on your Windows computer.

## System Requirements

- Windows 10 or later (64-bit recommended)
- 4GB RAM or more
- 100MB free disk space
- Screen resolution of 1280x720 or higher
- Game running in windowed or borderless windowed mode

## Installation Steps

### 1. Download the Application

- Download the `SpellCaster_v1.0.0.zip` file from the provided link

### 2. Extract the Files

- Right-click on the downloaded ZIP file and select "Extract All..."
- Choose a location where you want to extract the files, such as your Documents folder or Desktop
- Click "Extract" to extract the files

### 3. Run the Application

- Navigate to the extracted folder
- Find and double-click on `SpellCaster.exe` to start the application
- If a Windows security warning appears, click "More info" and then "Run anyway"
- If a User Account Control (UAC) prompt appears, click "Yes" to allow the application to run with administrator privileges (needed for keyboard control)

### 4. First-Time Setup

The first time you run the application, a setup wizard will guide you through the configuration process:

1. **Welcome Screen**: Click "Next" to begin setup
2. **Define Scan Area**: 
   - Position your game window so that the spell icons are visible
   - Click "Capture Screen" and select the area where your leftmost spell icon appears
   - Click "Next" when done
3. **Capture Spell Icons**: 
   - Capture templates for the spells you want to detect
   - For each spell, enter a name and click "Capture Icon"
   - Click "Next" when done
4. **Configure Keybinds**: 
   - Assign keyboard keys to each captured spell
   - These keys will be pressed when the corresponding spell is detected
   - Click "Next" when done
5. **Game-Specific Settings**:
   - Select your game type and resolution
   - Adjust key press duration if needed
   - Click "Next" when done
6. **Completion**: 
   - Click "Finish" to complete the setup and start using the application

## Using the Application

- Click "Start Casting" in the main window to begin detection
- The application will monitor the defined screen area and press the configured keys when spell icons are detected
- Use F10 to quickly toggle casting on/off
- Use F11 to hide/show the application window
- You can minimize to system tray for unobtrusive operation

## Troubleshooting

### Application Won't Start

- Make sure you have extracted all files from the ZIP
- Try running as administrator (right-click > Run as administrator)
- Check if your antivirus is blocking the application

### Spells Not Being Detected

- Make sure your game is running in windowed mode
- Verify that the scan area correctly includes the spell icon
- Try increasing the detection frequency in the settings
- Try decreasing the confidence threshold if spells aren't being detected

### Keys Not Being Pressed

- Some games may require administrator privileges for keybinds to work correctly
- Make sure the application is running as administrator
- Verify that the keybinds are correctly configured
- Try increasing the key press duration in the settings

### Performance Issues

- Reduce the detection frequency if CPU usage is too high
- Close unnecessary background applications
- Make sure your display scaling is set to 100% in Windows settings

## Uninstallation

To uninstall Spell Caster:

1. Close the application
2. Delete the folder where you extracted the application files
3. No registry entries or system files are modified by this application

## Support

If you need further assistance, please contact the developer with:
- A description of your problem
- Screenshots of your configuration
- Steps to reproduce the issue

---

Happy gaming!