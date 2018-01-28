import os
from importlib import import_module


class PluginManager():
    def __init__(self):
        self.modules = []


    def load_plugins(self, directory):
        for name in os.listdir(directory):
            if name.endswith(".py"):
                module_name = name[:-3]
                print("Loading {}".format(name))
                self.modules.append(import_module("plugins." + module_name))

    def run_plugins(self):
        for module in self.modules:
            module.say()

