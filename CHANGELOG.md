# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.0] - 2025-08-16

### Added
- **Multi-Engine Architecture**: 5 specialized cleaning engines
  - Standard Engine: Basic file cleaning
  - Optimized Engine: High-performance algorithms
  - Deep Engine: Advanced deep scanning
  - Super Engine: Maximum space liberation
  - System Optimizer: Performance optimization
- **13 Cleaning Categories**: Comprehensive categorization system
  - Quick Temp Files
  - Browser Cache
  - System Files
  - Development Tools
  - Media Downloads
  - Gaming Platforms
  - System Optimization
  - Recycle Bin
  - Full Standard Clean
  - Deep Aggressive Clean
  - Smart Deep Clean
  - Nuclear Clean
  - System Optimizer
- **Enhanced Safety Features**:
  - Smart file detection
  - Admin privilege handling
  - Progress tracking with real-time updates
  - Detailed error reporting
- **Professional UI**:
  - Colorized console output
  - Progress bars and animations
  - Interactive confirmation prompts
  - Comprehensive statistics display
- **Build System**:
  - Multiple build methods (batch, Python, PyInstaller)
  - Automated dependency management
  - Professional executable packaging
- **Documentation**:
  - Comprehensive README (English/Chinese)
  - Build instructions
  - Safety guidelines

### Changed
- **Complete Rewrite**: Rebuilt from ground up for Python 3.7+
- **Performance**: Significantly improved cleaning speed with multi-threading
- **Architecture**: Modular design with separate engines
- **Safety**: Enhanced file protection mechanisms
- **UI/UX**: Modern terminal interface with colors and progress indication

### Fixed
- Memory usage optimization
- Better error handling and recovery
- Improved file permission handling
- Enhanced compatibility with Windows 10/11

### Security
- Safe file deletion with verification
- Admin privilege validation
- Smart file type detection
- Protection against system file deletion

## [2.0.0] - Previous Version
### Features
- Basic C drive cleaning
- Simple category system
- Command-line interface

## [1.0.0] - Initial Release
### Features
- Basic temporary file cleaning
- Simple console output
- Windows compatibility

---

## Release Notes

### v3.0.0 Release Highlights

🚀 **Major Performance Boost**: Up to 5x faster cleaning with multi-engine architecture

🛡️ **Enhanced Safety**: Smart detection prevents accidental deletion of important files

🎯 **Precision Cleaning**: 13 specialized categories for targeted cleaning

⚡ **Professional Tools**: Multiple build methods and comprehensive documentation

💼 **Enterprise Ready**: Suitable for both personal and professional use

### Breaking Changes from v2.x
- Requires Python 3.7+ (previously supported 2.7)
- New command-line interface
- Configuration file format changed
- Some cleaning categories renamed for clarity

### Migration Guide
For users upgrading from v2.x:
1. Backup your current settings
2. Install new dependencies: `pip install -r requirements.txt`
3. Review new cleaning categories
4. Test with dry-run mode first

### Known Issues
- Some antivirus software may flag executable as suspicious (false positive)
- Windows Defender SmartScreen may require explicit permission
- Very large temp directories may take longer to process

### Upcoming Features (v3.1.0)
- Scheduled cleaning tasks
- Custom cleaning profiles
- Network drive support
- Enhanced logging system
- GUI version (Windows only)