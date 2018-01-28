from plugins.plugin import SarlaccPlugin

class Plugin(SarlaccPlugin):
    def stop(self):
        self.logger.info("Stopping")
