from abc import ABC, abstractmethod

class VideoSource(ABC):
  """
  Abstract class for video source.
  """
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
  """
  Abstract class for video frame target.
  """
  @abstractmethod
  def get_target(self) -> (int, int):
      pass

class FrameUpdater(ABC):
  """
  Abstract class for frame updater.
  """    
  @abstractmethod
  def get_updated_frame(self):
      pass