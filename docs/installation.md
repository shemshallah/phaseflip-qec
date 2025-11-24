# Installation Guide - PhaseFlip QEC

Complete installation instructions for the PhaseFlip Quantum Error Correction package.

---

## Requirements

### System Requirements
- **Python**: 3.8 or higher
- **Operating System**: Windows, macOS, or Linux
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Disk Space**: ~500MB for package and dependencies

### Required Dependencies
- `qiskit >= 0.39.0`
- `numpy >= 1.20.0`
- `matplotlib >= 3.4.0`
- `scipy >= 1.7.0`

### Optional Dependencies
- `scikit-learn >= 1.0.0` (for ML decoder)
- `jupyter >= 1.0.0` (for notebooks)
- `pytest >= 7.0.0` (for running tests)

---

## Installation Methods

### Method 1: Install from PyPI (Recommended)

```bash
pip install phaseflip-qec
```

This will install the latest stable release with all required dependencies.

### Method 2: Install from Source

#### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/phaseflip-qec.git
cd phaseflip-qec
```

#### Step 2: Create Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

#### Step 3: Install Package
```bash
# Install in development mode
pip install -e .

# Or install normally
pip install .
```

### Method 3: Install with Optional Dependencies

```bash
# Install with ML decoder support
pip install phaseflip-qec[ml]

# Install with development tools
pip install phaseflip-qec[dev]

# Install with all features
pip install phaseflip-qec[all]
```

---

## Verify Installation

After installation, verify everything is working:

```python
import phaseflip_qec
from phaseflip_qec.encoders import Distance3Encoder

# Create encoder
encoder = Distance3Encoder()

# Check version
print(f"PhaseFlip QEC version: {phaseflip_qec.__version__}")

# Create test circuit
circuit = encoder.encode()
print(f"✓ Installation successful! Created circuit with {circuit.num_qubits} qubits")
```

Expected output:
```
PhaseFlip QEC version: 1.0.0
✓ Installation successful! Created circuit with 3 qubits
```

---

## Installation for Different Use Cases

### For Researchers & Algorithm Developers
```bash
# Full installation with development tools
git clone https://github.com/yourusername/phaseflip-qec.git
cd phaseflip-qec
pip install -e ".[dev]"

# Install Jupyter for interactive development
pip install jupyter
```

### For Production Use
```bash
# Minimal installation
pip install phaseflip-qec

# With specific version pinning
pip install phaseflip-qec==1.0.0
```

### For ML Decoder Research
```bash
# Install with machine learning support
pip install phaseflip-qec[ml]

# Additional ML tools
pip install tensorflow  # or pytorch
```

---

## Platform-Specific Instructions

### Windows

```bash
# Install Python 3.8+ from python.org
# Open Command Prompt or PowerShell

pip install phaseflip-qec

# If you encounter SSL errors:
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org phaseflip-qec
```

### macOS

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.9

# Install package
pip3 install phaseflip-qec
```

### Linux (Ubuntu/Debian)

```bash
# Update package list
sudo apt update

# Install Python and pip
sudo apt install python3 python3-pip

# Install package
pip3 install phaseflip-qec
```

---

## Troubleshooting

### Issue: ImportError for Qiskit

**Solution:**
```bash
pip install --upgrade qiskit
```

### Issue: Matplotlib Backend Errors

**Solution (Linux):**
```bash
sudo apt install python3-tk
```

**Solution (macOS):**
```bash
brew install python-tk
```

### Issue: Permission Denied

**Solution:**
```bash
# Install in user directory
pip install --user phaseflip-qec
```

### Issue: Dependency Conflicts

**Solution:**
```bash
# Create clean virtual environment
python -m venv clean_env
source clean_env/bin/activate  # On Windows: clean_env\Scripts\activate
pip install phaseflip-qec
```

### Issue: Slow Installation

**Solution:**
```bash
# Use faster mirror
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple phaseflip-qec
```

---

## Updating PhaseFlip QEC

### Update to Latest Version
```bash
pip install --upgrade phaseflip-qec
```

### Update to Specific Version
```bash
pip install --upgrade phaseflip-qec==1.1.0
```

### Check Current Version
```python
import phaseflip_qec
print(phaseflip_qec.__version__)
```

---

## Uninstallation

```bash
pip uninstall phaseflip-qec
```

---

## Docker Installation (Advanced)

For isolated environment:

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install PhaseFlip QEC
RUN pip install phaseflip-qec

# Copy your code
COPY . /app

CMD ["python", "your_script.py"]
```

Build and run:
```bash
docker build -t phaseflip-qec .
docker run phaseflip-qec
```

---

## Next Steps

After successful installation:

1. **Quick Start**: Read the [Quick Start Guide](quickstart.md)
2. **Examples**: Explore the `examples/` directory
3. **API Reference**: Review [API Documentation](api_reference.md)
4. **Benchmarks**: Check [Performance Benchmarks](performance_benchmarks.md)

---

## Getting Help

If you encounter issues:

1. **Check Documentation**: Review this guide and the FAQ
2. **GitHub Issues**: Search existing issues at `github.com/yourusername/phaseflip-qec/issues`
3. **Create Issue**: If problem persists, create a new issue with:
   - Python version (`python --version`)
   - OS and version
   - Error message and stack trace
   - Minimal reproducible example

---

## Development Installation

For contributing to PhaseFlip QEC:

```bash
# Clone repository
git clone https://github.com/yourusername/phaseflip-qec.git
cd phaseflip-qec

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest tests/

# Run linting
flake8 phaseflip_qec/
black phaseflip_qec/
```

---

**Installation complete!** 🎉 

You're now ready to use PhaseFlip QEC for quantum error correction research and development.