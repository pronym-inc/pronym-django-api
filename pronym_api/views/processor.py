class Processor:
    def __init__(self, view, validator):
        self.view = view
        self.validator = validator

    def process(self):  # pragma: no cover
        pass


class NullProcessor(Processor):
    pass


class SaveValidatorProcessor(Processor):
    def process(self):
        return self.validator.save()
