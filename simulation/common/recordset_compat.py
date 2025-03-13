"""RecordSet utilities."""


from . import Array, ConfigsRecord, MetricsRecord, ParametersRecord, RecordSet
from .typing import (
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
)


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
