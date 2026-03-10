# Building InboxAgent for Windows

This guide provides step-by-step instructions on how to compile InboxAgent into a native Windows executable (`.exe`) and package it into a standard Windows Installer (`Setup.exe`). 

Due to complex C++ dependencies required by the GUI framework (PyQt6), **InboxAgent must be compiled directly on a Windows machine** to ensure all graphical libraries (DLLs) are correctly linked and packaged. Cross-compiling from Linux/Mac via Wine is not supported for the GUI version.

## Prerequisites

Before you begin, ensure you have the following installed on your Windows machine:

1. **Python 3.10 or newer**: Download from [python.org](https://www.python.org/downloads/).
   * *Important: During installation, ensure you check the box that says "Add Python to PATH".*
2. **Git**: Download from [git-scm.com](https://git-scm.com/download/win).
3. **NSIS (Nullsoft Scriptable Install System)**: Download from [nsis.sourceforge.io](https://nsis.sourceforge.io/Download). 
   * *This is only required if you want to build the final `Setup_x64.exe` installer wizard.*

---

## Step 1: Clone the Repository

Open a Terminal (Command Prompt or PowerShell) and clone the repository to your local machine:

```powershell
git clone https://github.com/rajatalha150/InboxAgent.git
cd InboxAgent
```

## Step 2: Set Up a Virtual Environment (Recommended)

It is highly recommended to build within an isolated Python virtual environment to prevent dependency conflicts.

```powershell
# Create the virtual environment
python -m venv venv

# Activate the virtual environment
# On Command Prompt:
venv\Scripts\activate.bat
# On PowerShell:
.\venv\Scripts\Activate.ps1
```

## Step 3: Install Dependencies

Install the project along with its GUI and packaging dependencies.

```powershell
pip install -e .[gui,packaging]
```

## Step 4: Compile the Executable (PyInstaller)

Navigate to the `packaging` directory and use PyInstaller with the provided configuration file (`open-email.spec`).

```powershell
cd packaging
pyinstaller --clean open-email.spec
```

This compilation process will take a few minutes. Once completed successfully, an `inbox-agent` folder will be generated inside `packaging\dist\`. 

You can test the compiled application immediately by double-clicking:
`packaging\dist\inbox-agent\inbox-agent.exe`

## Step 5: Build the Windows Installer (NSIS)

If you want to package the application into a professional, redistributable Windows setup wizard (`InboxAgent_Setup_0.1.0_x64.exe`), you will compile the NSIS script.

Make sure you have completed **Step 4** (the `dist\inbox-agent` folder must exist).

**Method A: Using Windows Explorer (Easiest)**
1. Open Windows File Explorer and navigate to the `InboxAgent\packaging` folder.
2. Right-click on the `installer.nsi` file.
3. Select **"Compile NSIS Script"**. 
4. A compiler window will open and build the installer.

**Method B: Using the Command Line**
If you added NSIS to your PATH or are using a continuous integration environment:

```powershell
makensis installer.nsi
```

## Output

Once the NSIS compilation is complete, you will find your final installer file in the `packaging` folder:

`InboxAgent_Setup_0.1.0_x64.exe`

You can now distribute this installer. When run, it will install the application to the user's `Program Files`, create Start Menu shortcuts, and handle the desktop icon.
