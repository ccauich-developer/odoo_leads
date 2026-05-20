from abc import ABC, abstractmethod

class BaseLeadProcessor(ABC):
    """
    Clase abstracta para asegurar que todos los drivers (FB, WA, IG)
    tengan el mismo método de procesamiento.
    """

    def __init__(self, env, log_record):
        self.env = env
        self.log_record = log_record

    @abstractmethod
    def process_payload(self, data):
        """Este método debe ser implementado por cada red social específica."""
        pass