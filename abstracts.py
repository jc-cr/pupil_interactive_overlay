from abc import ABC, abstractmethod

class VideoSource(ABC):

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def start_capture(self):
        pass

    @abstractmethod
    def get_frame(self):
        pass

    @abstractmethod
    def terminate(self):
        pass

class VideoFrameTarget(ABC):

    @abstractmethod
    def get_target(self) -> (int, int):
        pass
