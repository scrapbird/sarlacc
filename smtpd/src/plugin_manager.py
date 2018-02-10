import os
import logging
import traceback
from importlib import import_module
from enum import Enum


logger = logging.getLogger()


class PluginManager():
    def __init__(self, loop):
        self.loop = loop
        self.plugins = []


    def load_plugins(self, directory):
        for name in os.listdir(os.path.dirname(os.path.abspath(__file__)) + "/" + directory):
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


    def run_plugins(self):
        for plugin in self.plugins:
            plugin.stop()


    async def emit_new_email_address(self, *args, **kwargs):
        for plugin in self.plugins:
            self.loop.create_task(plugin.new_email_address(*args, **kwargs))


    async def emit_new_attachment(self, *args, **kwargs):
        for plugin in self.plugins:
            self.loop.create_task(plugin.new_attachment(*args, **kwargs))


    async def emit_new_mail_item(self, *args, **kwargs):
        for plugin in self.plugins:
            self.loop.create_task(plugin.new_mail_item(*args, **kwargs))

