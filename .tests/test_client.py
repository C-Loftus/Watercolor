import pytest
import sys

# Talon autoloads python files unless they start with "." and we want it to ignore the server directory
# Thus, we import this way since we can't import packages normally that start with a "."
sys.path.append("client")
from client import atspi_client
