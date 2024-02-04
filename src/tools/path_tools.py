import os
from pathlib import Path

class PathTools:
    def __init__(self):
        self.rootdir = self.get_root_dir()

    def get_root_dir(self) -> Path:
        path = os.path.realpath(__file__)   # User/username/..../llm_character_network/......./this_file.py
        pathlist = path.rsplit("/", 3)  # ["User", ..., "llm_character_network", "src", "data", "make_dataset.py"]
        rootdir = pathlist[0]
        return rootdir

    def get_target_dir(self, target_path:str) -> Path:
        """
        :param target_path: the path of the target directory or file from the root directory
        :return: absolute path of the target
        """
        if "llm_character_network" in target_path:
            ValueError("The path can take the following form:"
                       "- path from the root (project) directory")
        return Path(os.path.join(self.rootdir, target_path))

    def my_find(self, l, element):
        # reference: https://note.nkmk.me/python-list-index/
        if element in l:
            return l.index(element)
        else:
            return -1
