"""RecordSet utilities."""


from collections import OrderedDict
from collections.abc import Mapping
from typing import Union, get_args, cast

from . import Array, ConfigsRecord, MetricsRecord, ParametersRecord, RecordSet
from .typing import (
    ConfigsRecordValues,
    MetricsRecordValues,
    EvaluateIns,
    EvaluateRes,
    FitIns,
    FitRes,
    GetParametersIns,
    GetParametersRes,
    GetPropertiesIns,
    GetPropertiesRes,
    Parameters,
    Scalar,
    Status,
)


EMPTY_TENSOR_KEY = "_empty"


def parametersrecord_to_parameters(
    record: ParametersRecord, keep_input: bool
) -> Parameters:
    """Convert ParameterRecord to legacy Parameters.

    Warnings
    --------
    Because `Arrays` in `ParametersRecord` encode more information of the
    array-like or tensor-like data (e.g their datatype, shape) than `Parameters` it
    might not be possible to reconstruct such data structures from `Parameters` objects
    alone. Additional information or metadata must be provided from elsewhere.

    Parameters
    ----------
    record : ParametersRecord
        The record to be conveted into Parameters.
    keep_input : bool
        A boolean indicating whether entries in the record should be deleted from the
        input dictionary immediately after adding them to the record.

    Returns
    -------
    parameters : Parameters
        The parameters in the legacy format Parameters.
    """
    parameters = Parameters(tensors=[], tensor_type="")

    for key in list(record.keys()):
        if key != EMPTY_TENSOR_KEY:
            parameters.tensors.append(record[key].data)

        if not parameters.tensor_type:
            # Setting from first array in record. Recall the warning in the docstrings
            # of this function.
            parameters.tensor_type = record[key].stype

        if not keep_input:
            del record[key]


def parameters_to_parametersrecord(
    parameters: Parameters, keep_input: bool
) -> ParametersRecord:
    """Convert legacy Parameters into a single ParametersRecord.

    Because there is no concept of names in the legacy Parameters, arbitrary keys will
    be used when constructing the ParametersRecord. Similarly, the shape and data type
    won't be recorded in the Array objects.

    Parameters
    ----------
    parameters : Parameters
        Parameters object to be represented as a ParametersRecord.
    keep_input : bool
        A boolean indicating whether parameters should be deleted from the input
        Parameters object (i.e. a list of serialized NumPy arrays) immediately after
        adding them to the record.

    Returns
    -------
    ParametersRecord
        The ParametersRecord containing the provided parameters.
    """
    tensor_type = parameters.tensor_type

    num_arrays = len(parameters.tensors)
    ordered_dict = OrderedDict()
    for idx in range(num_arrays):
        if keep_input:
            tensor = parameters.tensors[idx]
        else:
            tensor = parameters.tensors.pop(0)
        ordered_dict[str(idx)] = Array(
            data=tensor, dtype="", stype=tensor_type, shape=[]
        )

    if num_arrays == 0:
        ordered_dict[EMPTY_TENSOR_KEY] = Array(
            data=b"", dtype="", stype=tensor_type, shape=[]
        )
    return ParametersRecord(ordered_dict, keep_input=keep_input)



def _check_mapping_from_recordscalartype_to_scalar(
    record_data: Mapping[str, Union[ConfigsRecordValues, MetricsRecordValues]]
) -> dict[str, Scalar]:
    """Check mapping `common.*RecordValues` into `common.Scalar` is possible."""
    for value in record_data.values():
        if not isinstance(value, get_args(Scalar)):
            raise TypeError(
                "There is not a 1:1 mapping between `common.Scalar` types and those "
                "supported in `common.ConfigsRecordValues` or "
                "`common.ConfigsRecordValues`. Consider casting your values to a type "
                "supported by the `common.RecordSet` infrastructure. "
                f"You used type: {type(value)}"
            )
    return cast(dict[str, Scalar], record_data)


def _recordset_to_fit_or_evaluate_ins_components(
    recordset: RecordSet,
    ins_str: str,
    keep_input: bool,
) -> tuple[Parameters, dict[str, Scalar]]:
    """Derive Fit/Evaluate Ins from a RecordSet."""
    # get Array and construct Parameters
    parameters_record = recordset.parameters_records[f"{ins_str}.parameters"]

    parameters = parametersrecord_to_parameters(
        parameters_record, keep_input=keep_input
    )

    # get config dict
    config_record = recordset.configs_records[f"{ins_str}.config"]
    # pylint: disable-next=protected-access
    config_dict = _check_mapping_from_recordscalartype_to_scalar(config_record)

    return parameters, config_dict


def _embed_status_into_recordset(
    res_str: str, status: Status, recordset: RecordSet
) -> RecordSet:
    status_dict: dict[str, ConfigsRecordValues] = {
        "code": int(status.code.value),
        "message": status.message,
    }
    # we add it to a `ConfigsRecord`` because the `status.message`` is a string
    # and `str` values aren't supported in `MetricsRecords`
    recordset.configs_records[f"{res_str}.status"] = ConfigsRecord(status_dict)
    return recordset


def recordset_to_evaluateins(recordset: RecordSet, keep_input: bool) -> EvaluateIns:
    """Derive EvaluateIns from a RecordSet object."""
    parameters, config = _recordset_to_fit_or_evaluate_ins_components(
        recordset,
        ins_str="evaluateins",
        keep_input=keep_input,
    )

    return EvaluateIns(parameters=parameters, config=config)


def recordset_to_fitins(recordset: RecordSet, keep_input: bool) -> FitIns:
    """Derive FitIns from a RecordSet object."""
    parameters, config = _recordset_to_fit_or_evaluate_ins_components(
        recordset,
        ins_str="fitins",
        keep_input=keep_input,
    )

    return FitIns(parameters=parameters, config=config)


def recordset_to_getparametersins(recordset: RecordSet) -> GetParametersIns:
    """Derive GetParametersIns from a RecordSet object."""
    config_record = recordset.configs_records["getparametersins.config"]
    # pylint: disable-next=protected-access
    config_dict = _check_mapping_from_recordscalartype_to_scalar(config_record)

    return GetParametersIns(config=config_dict)


def recordset_to_getpropertiesins(recordset: RecordSet) -> GetPropertiesIns:
    """Derive GetPropertiesIns from a RecordSet object."""
    config_record = recordset.configs_records["getpropertiesins.config"]
    # pylint: disable-next=protected-access
    config_dict = _check_mapping_from_recordscalartype_to_scalar(config_record)

    return GetPropertiesIns(config=config_dict)


def evaluateres_to_recordset(evaluateres: EvaluateRes) -> RecordSet:
    """Construct a RecordSet from a EvaluateRes object."""
    recordset = RecordSet()

    res_str = "evaluateres"
    # loss
    recordset.metrics_records[f"{res_str}.loss"] = MetricsRecord(
        {"loss": evaluateres.loss},
    )

    # num_examples
    recordset.metrics_records[f"{res_str}.num_examples"] = MetricsRecord(
        {"num_examples": evaluateres.num_examples},
    )

    # metrics
    recordset.configs_records[f"{res_str}.metrics"] = ConfigsRecord(
        evaluateres.metrics,  # type: ignore
    )

    # status
    recordset = _embed_status_into_recordset(
        f"{res_str}", evaluateres.status, recordset
    )

    return recordset


def fitres_to_recordset(fitres: FitRes, keep_input: bool) -> RecordSet:
    """Construct a RecordSet from a FitRes object."""
    recordset = RecordSet()

    res_str = "fitres"

    recordset.configs_records[f"{res_str}.metrics"] = ConfigsRecord(
        fitres.metrics  # type: ignore
    )
    recordset.metrics_records[f"{res_str}.num_examples"] = MetricsRecord(
        {"num_examples": fitres.num_examples},
    )
    recordset.parameters_records[f"{res_str}.parameters"] = (
        parameters_to_parametersrecord(
            fitres.parameters,
            keep_input,
        )
    )

    # status
    recordset = _embed_status_into_recordset(res_str, fitres.status, recordset)

    return recordset


def getparametersres_to_recordset(
    getparametersres: GetParametersRes, keep_input: bool
) -> RecordSet:
    """Construct a RecordSet from a GetParametersRes object."""
    recordset = RecordSet()
    res_str = "getparametersres"
    parameters_record = parameters_to_parametersrecord(
        getparametersres.parameters, keep_input=keep_input
    )
    recordset.parameters_records[f"{res_str}.parameters"] = parameters_record

    # status
    recordset = _embed_status_into_recordset(
        res_str, getparametersres.status, recordset
    )

    return recordset


def getpropertiesres_to_recordset(getpropertiesres: GetPropertiesRes) -> RecordSet:
    """Construct a RecordSet from a GetPropertiesRes object."""
    recordset = RecordSet()
    res_str = "getpropertiesres"
    recordset.configs_records[f"{res_str}.properties"] = ConfigsRecord(
        getpropertiesres.properties,  # type: ignore
    )
    # status
    recordset = _embed_status_into_recordset(
        res_str, getpropertiesres.status, recordset
    )

    return recordset
