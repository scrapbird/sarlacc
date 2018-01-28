import os
import logging
import traceback
from importlib import import_module


logger = logging.getLogger()


class PluginManager():
    def __init__(self):
        self.modules = []


    def load_plugins(self, directory):
        for name in os.listdir(directory):
            if name.endswith(".py"):
                module_name = name[:-3]
                try:
                    self.modules.append(import_module("plugins." + module_name))
                    logger.info("Loaded plugins/{}".format(name))
                except Exception as e:
                    logger.error("Failed to load plugin/{}".format(name))
                    logger.error(traceback.format_exc())

    def run_plugins(self):
        for module in self.modules:
            module.say()

