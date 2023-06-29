import abc

from metisfl.models.model_dataset import ModelDataset
from metisfl.models.types import LearningTaskStats, ModelWeightsDescriptor
from metisfl.proto import metis_pb2


class ModelOps(object):
    
    _model = None
    
    def get_model(self) -> object:
        return self._model

    @abc.abstractmethod
    def train_model(self,
                    train_dataset: ModelDataset,
                    learning_task_pb: metis_pb2.LearningTask,
                    hyperparameters_pb: metis_pb2.Hyperparameters,
                    validation_dataset: ModelDataset = None,
                    test_dataset: ModelDataset = None,
                    verbose=False) -> [ModelWeightsDescriptor, LearningTaskStats]:
        pass
    
    @abc.abstractmethod
    def evaluate_model(self,
                       eval_dataset: ModelDataset,
                       batch_size=100,
                       metrics=None,
                       verbose=False) -> dict:
        pass
    
    @abc.abstractmethod
    def infer_model(self,
                    infer_dataset: ModelDataset,
                    batch_size=100):
        pass
