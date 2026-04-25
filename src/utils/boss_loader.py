import json
import os
from typing import Dict


def load_boss_data() -> Dict:
    """Load boss data from bosses.json."""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    file_path = os.path.join(data_dir, "bosses.json")
    
    with open(file_path, "r") as f:
        return json.load(f)


def load_artifacts() -> Dict:
    """Load artifact data from artifacts.json."""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    file_path = os.path.join(data_dir, "artifacts.json")
    
    with open(file_path, "r") as f:
        return json.load(f)
