from plugins.plugin import SarlaccPlugin

class Plugin(SarlaccPlugin):
    def run(self):
        self.logger.info("This is an example plugin")
