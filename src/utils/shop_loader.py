import json
import os
from typing import Dict


def load_shop_data() -> Dict:
    """Load shop data from shop.json."""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    file_path = os.path.join(data_dir, "shop.json")
    
    with open(file_path, "r") as f:
        return json.load(f)
