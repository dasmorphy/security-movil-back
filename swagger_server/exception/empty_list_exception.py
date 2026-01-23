class EmptyListException(Exception):

    def __init__(self, message="Datos no encontrados", model=None):
        self.message = message + " para " + model if model else message
        super().__init__(self.message)
