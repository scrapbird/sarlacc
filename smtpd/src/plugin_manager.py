import os
import logging
import traceback
from importlib import import_module
from enum import Enum


logger = logging.getLogger()


class PluginManager():
    def __init__(self, loop):
        """Init method for PluginManager.

        Args:
            loop -- asyncio loop.
        """

        self.loop = loop
        self.plugins = []


    def load_plugins(self, store, directory):
        """Load plugins from plugin directory.

        store -- sarlacc store object (provides interface to backend storage).
        directory -- path to the directory to load plugins from.
        """

        for name in os.listdir(os.path.dirname(os.path.abspath(__file__)) + "/" + directory):
            if name.endswith(".py") and not name == "plugin.py":
                module_name = name[:-3]
                try:
                    module = import_module("plugins." + module_name)
                    self.plugins.append(module.Plugin(logger, store))
                    logger.info("Loaded plugins/{}".format(name))
                except Exception as e:
                    logger.error("Failed to load plugin/{}".format(name))
                    logger.error(traceback.format_exc())


    def run_plugins(self):
        """Run the plugins.

        Calls all the currently loaded plugin's `run` methods.
        """

        for plugin in self.plugins:
            plugin.run()


    def stop_plugins(self):
        """Stop the plugins.

        Calls all the currently loaded plugin's `stop` methods.
        """

        for plugin in self.plugins:
            plugin.stop()


    async def emit_new_email_address(self, *args, **kwargs):
        """Emit "new email address" signal.

        Inform all plugins that an email address that hasn't been seen before was detected.
        """

        for plugin in self.plugins:
            self.loop.create_task(plugin.new_email_address(*args, **kwargs))


    async def emit_new_attachment(self, *args, **kwargs):
        """Emit "new attachment" signal.

        Inform all plugins that a new attachment that hasn't been seen before was detected.
        """

        for plugin in self.plugins:
            self.loop.create_task(plugin.new_attachment(*args, **kwargs))


    async def emit_new_mail_item(self, *args, **kwargs):
        """Emit "new mail item" signal.

        Inform all plugins that a new email has been received.
        """

        for plugin in self.plugins:
            self.loop.create_task(plugin.new_mail_item(*args, **kwargs))

