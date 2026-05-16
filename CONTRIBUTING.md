# Contributing to Interview Analyzer

Thank you for your interest in contributing! This document provides guidelines for contributing to the project, especially for platform-specific testing and development.

## Platform-Specific Testing

Interview Analyzer is currently in different stages of support across platforms:

### Windows ✅ (Fully Supported)
- Primary development platform
- All features tested and working
- If you find bugs on Windows, please report them

### macOS 🔄 (Community Testing)
- Testing branch: `feature/macos-support`
- Focus: Audio capture via Core Audio or Soundflower
- Known limitations: System audio loopback setup required
- Help needed: Testing and debugging audio capture, dependency verification

### Linux 🔄 (Community Testing)
- Testing branch: `feature/linux-support`
- Focus: PulseAudio/ALSA integration
- Known limitations: Audio device configuration varies by distro
- Help needed: Testing across different distributions, audio setup documentation

## How to Contribute

### 1. Platform-Specific Bug Reports

When reporting issues, please include:
```
**Platform**: Windows/macOS/Linux
**OS Version**: [e.g., Windows 11, macOS 14.2, Ubuntu 22.04]
**Python Version**: 3.10, 3.11, 3.12, etc.
**Error Message**: [Full error traceback]
**Steps to Reproduce**: [Detailed steps]
**Setup**: [How you installed the app]
```

### 2. Testing a New Platform

```bash
# Create a feature branch
git checkout -b feature/platform-name-support

# Document your setup process
# Create platform-specific documentation if needed

# Test all features:
# - Audio capture (system audio or microphone)
# - STT (different languages)
# - Question detection
# - LLM providers
# - Session history
# - Screen capture

# Commit your findings
git add .
git commit -m "Test results for [platform name]"

# Submit PR for review
git push origin feature/platform-name-support
```

### 3. Audio Capture Implementation

If implementing audio capture for a new platform:

**File to modify**: `backend/audio/capture.py`

Current structure:
```python
import platform

if platform.system() == 'Windows':
    # Windows: PyAudioWPatch with WASAPI
    pass
elif platform.system() == 'Darwin':  # macOS
    # macOS: Core Audio or Soundflower
    pass
elif platform.system() == 'Linux':
    # Linux: PulseAudio
    pass
```

### 4. Setup Script Enhancements

If adding new OS-specific setup steps:

**File to modify**: `setup.py` and `requirements-[os].txt`

Example:
```python
def setup_audio_macos():
    """Setup audio capture for macOS"""
    print("[*] Setting up macOS audio capture...")
    # Platform-specific setup code
    pass
```

### 5. Documentation

For platform-specific notes, update:
- `README.md` - Installation and troubleshooting sections
- `backend/audio/README.md` (create if needed) - Audio capture details
- Platform-specific guides in `docs/` folder

## Code Style

### Python
- Follow PEP 8
- Use type hints for new code
- Add docstrings to functions and classes
- Use f-strings for formatting

### TypeScript/React
- Use consistent naming (camelCase for variables, PascalCase for components)
- Add JSDoc comments to functions
- Keep components focused and testable

### General
- Use meaningful commit messages
- One feature per pull request
- Include tests for new features
- Update documentation with changes

## Development Setup

### Windows
```bash
python -m venv .venv
.\.venv\Scripts\activate
python setup.py
```

### macOS
```bash
python3 -m venv .venv
source .venv/bin/activate
python3 setup.py
```

### Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
python3 setup.py
```

## Pull Request Process

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/your-feature`
3. **Make** your changes and commit with clear messages
4. **Test** thoroughly on your platform
5. **Push** to your fork
6. **Create** a Pull Request with:
   - Clear description of changes
   - Platform(s) tested on
   - Screenshots or logs if applicable
   - Any known limitations

## Testing Checklist

Before submitting a PR, verify:

- [ ] Code runs without errors on target platform
- [ ] No new warnings in console
- [ ] All dependencies listed in requirements
- [ ] Documentation is updated
- [ ] Commit messages are clear and descriptive
- [ ] No hardcoded paths or credentials
- [ ] Setup script works for fresh installation

## Known Platform Issues

### macOS
- Audio capture requires BlackHole or Soundflower installation
- Potential issues with unsigned/notarized code

### Linux
- Audio device configuration varies by distribution
- PulseAudio/ALSA compatibility varies
- Some dependencies may need system packages

### Windows
- WASAPI loopback device must be enabled
- Antivirus may block port binding
- Python encoding setup is critical

## Community Support

- Check existing Issues and Discussions
- Ask questions in Discussions tab
- Share your setup experience
- Help other users with similar platforms

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

Thank you for helping make Interview Analyzer better! 🙏
