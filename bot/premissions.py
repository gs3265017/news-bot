from typing import List
import os

class Permissions:
    def __init__(self):
        self.admins: List[int] = []
        self.editors: List[int] = []
        
    def load(self):
        self.admins = list(map(int, os.getenv("ADMIN_IDS").split(',')))
        self.editors = list(map(int, os.getenv("EDITOR_IDS", "").split(',')))