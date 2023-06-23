import os

from metisfl.learner.dataset_handler import LearnerDataset
from metisfl.models.model_dataset import (
    ModelDatasetClassification,
    ModelDatasetRegression,
)
from metisfl.utils.grpc_controller_client import GRPCControllerClient
from metisfl.proto import metis_pb2


class FederationHelper:
    def __init__(
        self,
        learner_server_entity: metis_pb2.ServerEntity,
        controller_server_entity: metis_pb2.ServerEntity,
        learner_dataset: LearnerDataset,
        learner_credentials_fp: str,
    ) -> None:
        self.learner_server_entity = learner_server_entity
        self.controller_server_entity = controller_server_entity
        self.learner_dataset = learner_dataset

        # The `learner_id` param is generated by the controller with the join federation request
        # and it is used thereafter for every incoming/forwarding request.
        self.__learner_credentials_fp = learner_credentials_fp
        if not os.path.exists(self.__learner_credentials_fp):
            os.mkdir(self.__learner_credentials_fp)

        # TODO if we want to be more secure, we can dump an
        #  encrypted version of auth_token and learner_id
        self.__learner_id_fp = os.path.join(
            self.__learner_credentials_fp, "learner_id.txt"
        )
        self.__auth_token_fp = os.path.join(
            self.__learner_credentials_fp, "auth_token.txt"
        )

        self._learner_controller_client = GRPCControllerClient(
            self.controller_server_entity, max_workers=1
        )

    def host_port_identifier(self):
        return "{}:{}".format(
            self.learner_server_entity.hostname, self.learner_server_entity.port
        )

    def join_federation(self):
        # TODO If I create a learner controller instance once (without channel initialization)
        #  then the program hangs!
        (
            train_dataset_meta,
            validation_dataset_meta,
            test_dataset_meta,
        ) = self.learner_dataset.load_datasets_metadata_subproc()
        is_classification = train_dataset_meta[2] == ModelDatasetClassification
        is_regression = train_dataset_meta[2] == ModelDatasetRegression

        (
            self.__learner_id,
            self.__auth_token,
            status,
        ) = self._learner_controller_client.join_federation(
            self.learner_server_entity,
            self.__learner_id_fp,
            self.__auth_token_fp,
            train_dataset_meta[0],
            train_dataset_meta[1],
            validation_dataset_meta[0],
            validation_dataset_meta[1],
            test_dataset_meta[0],
            test_dataset_meta[1],
            is_classification,
            is_regression,
        )
        return status

    def mark_learning_task_completed(self, training_future):
        # If the returned future was completed successfully and was not cancelled,
        # meaning it did complete its running job, then notify the controller.
        if training_future.done() and not training_future.cancelled():
            completed_task_pb = training_future.result()
            self._learner_controller_client.mark_task_completed(
                learner_id=self.__learner_id,
                auth_token=self.__auth_token,
                completed_task_pb=completed_task_pb,
                block=False,
            )

    def leave_federation(self):
        status = self._learner_controller_client.leave_federation(
            self.__learner_id, self.__auth_token, block=False
        )
        # Make sure that all pending tasks have been processed.
        self._learner_controller_client.shutdown()
        return status
