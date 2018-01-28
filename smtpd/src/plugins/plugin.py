class SarlaccPlugin:
    def __init__(self, logger):
        self.logger = logger

    def run(self):
        self.logger.info("Test")

    def stop(self):
        pass
