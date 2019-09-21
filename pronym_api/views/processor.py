class Processor:
    def __init__(self, view, validator):
        self.view = view
        self.validator = validator

    def process(self):
        pass


class NullProcessor(Processor):
    pass


class SaveValidatorProcessor(Processor):
    def process(self):
        return self.validator.save()
