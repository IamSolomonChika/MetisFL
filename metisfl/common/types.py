import os
import yaml

from dataclasses import dataclass
from typing import List, Optional
from metisfl.common.formatting import DataTypeFormatter

METRICS = ["accuracy"]
COMMUNICATION_PROTOCOLS = ["Synchronous", "Asynchronous", "SemiSynchronous"]
MODEL_STORES = ["InMemory", "Redis"]
HE_SCHEMES = ["CKKS"]
AGGREGATION_RULES = ["FedAvg", "FedRec", "FedStride", "SecAgg"]
SCALING_FACTORS = ["NumTrainingExamples",
                   "NumCompletedBatches", "NumParticipants"]


@dataclass
class TerminationSingals(object):
    """Set of termination signals for the federated training. Controls when the training is terminated.

    Parameters
    ----------
    federation_rounds : Optional[int], (default=None)
        Number of federation rounds to run. I
    execution_cutoff_time_mins : Optional[int], (default=None)
        Maximum execution time in minutes. 
    evaluation_metric : Optional[str], (default=None)
        The evaluation metric to use for early stopping. 
        The metric must be one returned by the Learner train() method.
    evaluation_metric_cutoff_score : Optional[float], (default=None)
        The evaluation metric cutoff score for early stopping.

    Raises
    ------
    ValueError
        If the evaluation metric is not one of the following: ["accuracy"].
    """

    federation_rounds:  Optional[int] = None
    execution_cutoff_time_mins: Optional[int] = None
    evaluation_metric: Optional[str] = None
    evaluation_metric_cutoff_score: Optional[float] = None

    @classmethod
    def from_yaml(cls, yaml_dict: dict) -> 'TerminationSingals':
        yaml_dict = DataTypeFormatter.camel_to_snake_dict_keys(yaml_dict)
        return cls(**yaml_dict)

        # FIXME make sure one is defined


@dataclass
class ModelStoreConfig(object):
    """Configuration for the model store. Controls how the model store is used.

    Parameters
    ----------
    model_store : str
        The model store to use. Must be one of the following: ["InMemory", "Redis"].
    lineage_length : int
        The max number of models to store before start evicting models. If 0, no eviction is performed.
    model_store_hostname : Optional[str], (default=None)
        The hostname of the model store. Required if the model store is Redis.
    model_store_port : Optional[int], (default=None)
        The port of the model store. Required if the model store is Redis.


    Raises
    ------
    ValueError
        Value error is raised in the following cases:
        - If the model store is not one of the following: ["InMemory", "Redis"].
        - If the model store is Redis and the hostname or port are not specified.
    """

    model_store: str
    lineage_length: int
    model_store_hostname: Optional[str] = None
    model_store_port: Optional[int] = None

    @classmethod
    def from_yaml(cls, yaml_dict: dict) -> 'ModelStoreConfig':
        yaml_dict = DataTypeFormatter.camel_to_snake_dict_keys(yaml_dict)
        return cls(**yaml_dict)

    def __post_init__(self):
        if self.model_store not in MODEL_STORES:
            raise ValueError(f"Invalid model store: {self.model_store}")
        if self.model_store == "Redis":
            if self.model_store_hostname is None:
                raise ValueError(
                    "Redis model store requires a hostname to be specified")
            if self.model_store_port is None:
                raise ValueError(
                    "Redis model store requires a port to be specified")


@dataclass
class GlobalTrainConfig(object):
    """Configuration for the global training. Sets basic parameters reqired for the federated training.

    Parameters
    ----------
    aggregation_rule : str
        The aggregation rule to use. Must be one of the following: ["FedAvg", "FedRec", "FedStride", "SecAgg"].
    communication_protocol : str
        The communication protocol to use. Must be one of the following: ["Synchronous", "Asynchronous", "SemiSynchronous"].
    scaling_factor : str
        The scaling factor to use. Must be one of the following: ["NumTrainingExamples", "NumCompletedBatches", "NumParticipants"].
    participation_ratio : Optional[float], (default=1.0)
        The participation ratio to use. Defaults to 1.0.
    stride_length : Optional[int], (default=None)
        The stride length to use. Required if the aggregation rule is FedStride.
    he_batch_size : Optional[int], (default=None)
        The HE batch size to use. Required if the aggregation rule is SecAgg.
    he_scaling_factor_bits : Optional[int], (default=None)
        The HE scaling factor bits to use. Required if the aggregation rule is SecAgg.
    semi_sync_lambda : Optional[float], (default=None)
        The semi-sync lambda to use. Required if the communication protocol is SemiSynchronous.
    semi_sync_recompute_num_updates : Optional[int], (default=None)
        The semi-sync recompute num updates to use. Required if the communication protocol is SemiSynchronous.

    Raises
    ------
    ValueError
        Value error is raised in the following cases:
        - If the aggregation rule is not one of the following: ["FedAvg", "FedRec", "FedStride", "SecAgg"].
        - If the communication protocol is not one of the following: ["Synchronous", "Asynchronous", "SemiSynchronous"].
        - If the scaling factor is not one of the following: ["NumTrainingExamples", "NumCompletedBatches", "NumParticipants"].
        - If the communication protocol is SemiSynchronous and the semi_sync_lambda or semi_sync_recompute_num_updates are not specified.

    """

    aggregation_rule: str
    communication_protocol: str
    scaling_factor: str
    participation_ratio: Optional[float] = 1.0
    stride_length: Optional[int] = None
    he_batch_size: Optional[int] = None
    he_scaling_factor_bits: Optional[int] = None
    he_crypto_context_file: Optional[str] = None
    semi_sync_lambda: Optional[float] = None
    semi_sync_recompute_num_updates: Optional[int] = None

    @classmethod
    def from_yaml(cls, yaml_dict: dict) -> 'GlobalTrainConfig':
        yaml_dict = DataTypeFormatter.camel_to_snake_dict_keys(yaml_dict)
        return cls(**yaml_dict)

    def __post_init__(self):
        if self.aggregation_rule not in AGGREGATION_RULES:
            raise ValueError(
                f"Invalid aggregation rule: {self.aggregation_rule}")
        if self.communication_protocol not in COMMUNICATION_PROTOCOLS:
            raise ValueError(
                f"Invalid communication protocol: {self.protocol}")
        if self.scaling_factor not in SCALING_FACTORS:
            raise ValueError(f"Invalid scaling factor: {self.scaling_factor}")
        if self.he_crypto_context_file is not None and not os.path.isfile(self.he_crypto_context_file):
            raise ValueError(
                f"HE crypto context file {self.he_crypto_context_file} does not exist")


@dataclass
class LocalTrainConfig(object):
    """Configuration for the local training. Sets basic parameters for the local training.

    Parameters
    ----------
    batch_size : int
        The batch size te be used by the Leareners
    epochs : int
        The number of local epochs to be used by the Leareners.

    """

    batch_size: int
    epochs: int

    @classmethod
    def from_yaml(cls, yaml_dict):
        yaml_dict = DataTypeFormatter.camel_to_snake_dict_keys(yaml_dict)
        return cls(**yaml_dict)


@dataclass
class ServerParams(object):
    """Server parameters for starting the Controller and Learners servers. 
        If the certificates and the private key are specified, the connection is secure. 

    Parameters
    ----------
    hostname : str
        The hostname of the server.
    port : int
        The port of the server.
    root_certificate : Optional[str], (default=None)
        The root certificate file of the server.
    server_certificate : Optional[str], (default=None)
        The server certificate file of the server.
    private_key : Optional[str], (default=None)
        The private key file of the server.

    Raises
    ------
    ValueError
        Value error is raised in the following cases:
        - If any of the certificates or the private key files does not exist.
        - If any but not all of the certificates or the private key files are specified.
    """

    hostname: str
    port: int
    # TODO: verify that the certificates and the private key are valid
    root_certificate: Optional[str] = None
    server_certificate: Optional[str] = None
    private_key: Optional[str] = None

    @classmethod
    def from_yaml(cls, yaml_dict: dict) -> 'ServerParams':
        yaml_dict = DataTypeFormatter.camel_to_snake_dict_keys(yaml_dict)
        return cls(**yaml_dict)

    def __post_init__(self):
        crt, serv, key = self.root_certificate, self.server_certificate, self.private_key
        if crt is not None and not os.path.isfile(crt):
            raise ValueError(
                f"Root certificate file {crt} does not exist")
        if serv is not None and not os.path.isfile(serv):
            raise ValueError(
                f"Server certificate file {serv} does not exist")
        if key is not None and not os.path.isfile(key):
            raise ValueError(
                f"Private key file {key} does not exist")
        if not all([crt, serv, key]) and \
                any([crt, serv, key]):
            raise ValueError(
                "All of the following must be specified: root certificate, server certificate, private key")


@dataclass
class ClientParams(object):
    """Server parameters for connecting to the Controller and Learners servers.

    Parameters
    ----------
    hostname : str
        The hostname of the server.
    port : int
        The port of the server.
    root_certificate : Optional[str], (default=None)
        The root certificate file of the server. If not specified, the connection is insecure.

    Raises
    ------
    ValueError
        Value error is raised in the following cases:
        - If the root certificate file does not exist.
    """

    hostname: str
    port: int
    root_certificate: Optional[str] = None

    @classmethod
    def from_yaml(cls, yaml_dict: dict) -> 'ClientParams':
        yaml_dict = DataTypeFormatter.camel_to_snake_dict_keys(yaml_dict)
        return cls(**yaml_dict)

    def __post_init__(self):
        if self.root_certificate is not None and not os.path.isfile(self.root_certificate):
            raise ValueError(
                f"Root certificate file {self.root_certificate} does not exist")


KEY_TO_CLASS = {
    "global_train_config": GlobalTrainConfig,
    "termination_signals": TerminationSingals,
    "model_store_config": ModelStoreConfig,
    "local_train_config": LocalTrainConfig,
}


@dataclass
class FederationEnvironment(object):
    """MetisFL federated training environment configuration."""

    global_train_config: GlobalTrainConfig
    termination_signals: TerminationSingals
    model_store_config: ModelStoreConfig
    local_train_config: LocalTrainConfig

    controller: ServerParams
    learners: List[ServerParams]

    @classmethod
    def from_yaml(cls, yaml_file: str) -> 'FederationEnvironment':
        """Generates a FederationEnvironment object from a yaml file.

        Parameters
        ----------
        yaml_file : str
            The yaml file to load the FederationEnvironment from.

        Returns
        -------
        FederationEnvironment
            The FederationEnvironment object.
        """

        yaml_dict = yaml.safe_load(open(yaml_file, 'r'))

        yaml_dict = DataTypeFormatter.camel_to_snake_dict_keys(yaml_dict)

        for key, value in yaml_dict.items():
            if key in KEY_TO_CLASS:
                yaml_dict[key] = KEY_TO_CLASS[key].from_yaml(value)

        yaml_dict['controller'] = ServerParams.from_yaml(
            yaml_dict['controller'])

        yaml_dict['learners'] = [ServerParams.from_yaml(
            learner) for learner in yaml_dict['learners']]

        return cls(**yaml_dict)
