# This is the definitive entry point for the packaged application.
# It ensures that the bundled 'src' directory is on the Python path at runtime.
import sys
import os

# When running as a PyInstaller bundle, the 'src' directory is at the root
# of the unpacked temporary folder (_MEIPASS).
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    sys.path.insert(0, os.path.join(sys._MEIPASS, 'src'))

from open_email.main import main

if __name__ == "__main__":
    main()
