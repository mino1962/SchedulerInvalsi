import sys
import os

# Ensure src is in path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.gui import InvalsiApp

VERSION = "260331.0"

if __name__ == "__main__":
    app = InvalsiApp(version=VERSION)
    app.mainloop()
