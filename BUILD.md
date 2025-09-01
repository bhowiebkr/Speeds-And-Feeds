# Build Instructions

This document describes how to build the Speeds and Feeds Calculator using Nuitka for distribution.

## Prerequisites

- Python 3.11
- Virtual environment with requirements installed
- Git for version tagging

## Local Development Build

1. **Install build dependencies**:
```bash
pip install -r requirements.txt
```

2. **Run local build**:
```bash
cd src
python -m nuitka ^
  --standalone ^
  --enable-plugin=pyside6 ^
  --include-qt-plugins=platforms,styles,iconengines ^
  --output-dir=../build ^
  --output-filename=SpeedsAndFeeds.exe ^
  --windows-disable-console ^
  --remove-output ^
  --lto=yes ^
  --include-data-file=dark_theme.qss=src/dark_theme.qss ^
  ../main.py
```

3. **Test the build**:
```bash
cd build/main.dist
./SpeedsAndFeeds.exe
```

## Automated GitHub Actions Build

### Triggering Builds

**Automatic builds** happen on:
- Push to `main` branch
- Pull requests to `main` branch  
- Version tags (e.g., `v2.0.0`)

**Manual release** creation:
1. Create and push a version tag: `git tag v2.0.0 && git push origin v2.0.0`
2. Wait for the build to complete
3. Go to Actions → Create Release
4. Enter the tag name and release type
5. Run the workflow

### Build Artifacts

- **Standalone executable**: No Python installation required
- **Optimized**: LTO and Nuitka optimizations enabled
- **Professional**: Includes version info and company metadata
- **Clean packaging**: Automated zip creation for releases

## Build Configuration

### Nuitka Options

- `--standalone`: Creates self-contained executable
- `--enable-plugin=pyside6`: Includes PySide6 support
- `--include-qt-plugins`: Bundles required Qt plugins
- `--windows-disable-console`: GUI application (no console window)
- `--lto=yes`: Link-time optimization for smaller/faster executable
- `--remove-output`: Cleans up intermediate build files

### Included Files

- Application executable (`SpeedsAndFeeds.exe`)
- Qt libraries and plugins
- Dark theme stylesheet
- Build information JSON

## Troubleshooting

### Common Issues

1. **Missing DLLs**: Ensure all Qt plugins are included
2. **Import errors**: Check `--nofollow-import-to` exclusions
3. **Size issues**: Use `--lto=yes` for optimization
4. **Testing**: Always test on a clean Windows system

### Debug Mode

For debugging builds, remove these flags:
- `--windows-disable-console` (shows console output)
- `--remove-output` (keeps intermediate files)

## Release Process

1. **Development**: Make changes and test locally
2. **Version bump**: Update version in workflows if needed
3. **Tag**: Create version tag (`v2.0.0`, `v2.1.0`, etc.)
4. **Build**: GitHub Actions automatically builds on tag push
5. **Release**: Manually create release using GitHub Actions
6. **Distribution**: Download from GitHub Releases page