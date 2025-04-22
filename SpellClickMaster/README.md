# Spell Caster - Automatic Spell Detection and Casting

Spell Caster is a desktop application that detects spell icons on your game screen and automatically presses the corresponding keybinds to cast them. It's designed to help optimize your gameplay by automatically handling spell rotations based on visual cues.

## Features

- **Automatic Spell Detection**: Monitors a specified area of your screen for spell icons
- **Automatic Casting**: Presses the corresponding key when a spell icon is detected
- **Customizable Configuration**: Define which spells to detect and which keys to press
- **User-Friendly Interface**: Easy setup wizard to configure the application
- **Performance Monitoring**: Track detection rate and response time
- **Minimal System Requirements**: Low CPU and memory usage

## Quick Start Guide

1. **Download and Install**:
   - Download the latest version from the Releases page
   - Extract the ZIP file to a location of your choice
   - Run `SpellCaster.exe` to start the application

2. **Initial Setup**:
   - The first time you run the application, a setup wizard will guide you through the configuration process
   - Position your game window so that the spell icons are visible
   - Use the wizard to define the screen area to monitor (where the leftmost spell icon appears)
   - Configure keybinds for each detected spell

3. **Using the Application**:
   - Click "Start Casting" in the main window to begin detection
   - The application will monitor the defined screen area and press the configured keys when spell icons are detected
   - Use F10 to quickly toggle casting on/off
   - Use F11 to hide/show the application window

## Gaming Focus

Based on the provided screenshot, this application is optimized for detecting the leftmost spell icon (N5) in a 3-icon display (N5, C1, N1). The application will detect when a specific spell icon appears in the leftmost position and press the corresponding keybind.

## System Requirements

- Windows 10 or later
- 4GB RAM
- Screen resolution of 1280x720 or higher
- Game running in windowed or borderless windowed mode for best results

## Performance Tips

- Running your game in windowed mode provides the most reliable detection
- Adjust the detection frequency and confidence threshold to balance between responsiveness and accuracy
- For best performance, focus on detecting just the most critical spells
- Position your spell icons in a visually distinct area of the screen

## Troubleshooting

If you encounter any issues:

1. **Detection Problems**:
   - Make sure your game is running in windowed mode
   - Verify that the scan area correctly includes the spell icon
   - Try increasing the confidence threshold if you get false positives
   - Try decreasing the confidence threshold if spells aren't being detected

2. **Keybind Issues**:
   - Some games may require administrator privileges for keybindings to work correctly
   - Try running the application as administrator if key presses aren't registered
   - Make sure the key combinations don't conflict with other system shortcuts

3. **Performance Issues**:
   - Reduce the detection frequency if CPU usage is too high
   - Close unnecessary background applications
   - Make sure your display scaling is set to 100% in Windows settings

## Need Help?

If you need further assistance, please check the project repository for updates or submit an issue with:
- A description of your problem
- Screenshots of your configuration
- Steps to reproduce the issue

## License

This application is provided for personal use only. Please use responsibly and in accordance with the terms of service of your games.

---

*Note: This application interacts with your game by analyzing the screen and simulating keyboard input. It does not modify any game files or memory and does not violate anti-cheat systems that prohibit memory modification or code injection.*