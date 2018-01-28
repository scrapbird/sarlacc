import os
import logging
import traceback
from importlib import import_module


logger = logging.getLogger()


class PluginManager():
    def __init__(self):
        self.plugins = []


    def load_plugins(self, directory):
        for name in os.listdir(directory):
            if name.endswith(".py") and not name == "plugin.py":
                module_name = name[:-3]
                try:
                    module = import_module("plugins." + module_name)
                    self.plugins.append(module.Plugin(logger))
                    logger.info("Loaded plugins/{}".format(name))
                except Exception as e:
                    logger.error("Failed to load plugin/{}".format(name))
                    logger.error(traceback.format_exc())

    def run_plugins(self):
        for plugin in self.plugins:
            plugin.run()
            plugin.stop()

