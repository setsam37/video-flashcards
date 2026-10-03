class ProcessingError(Exception):
    def __init__(self,code,message):
        self.code=code;self.public_message=message
        super().__init__(message)
