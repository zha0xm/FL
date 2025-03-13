"""Client-side message handler."""


from logging import WARN

from client.client import (
    maybe_call_get_properties,
    maybe_call_get_parameters,
    maybe_call_fit, 
    maybe_call_evaluate,
)
from client.numpy_client import NumPyClient
from client.typing import ClientFnExt
from common import Message, Context, log
from common.constant import MessageType, MessageTypeLegacy
from common.recordset_compat import (
    evaluateres_to_recordset,
    fitres_to_recordset,
    getparametersres_to_recordset,
    getpropertiesres_to_recordset,
    recordset_to_evaluateins,
    recordset_to_fitins,
    recordset_to_getparametersins,
    recordset_to_getpropertiesins,
)


def handle_legacy_message_from_msgtype(
    client_fn: ClientFnExt, message: Message, context: Context
) -> Message:
    """Handle legacy message in the inner most mod."""
    client = client_fn(context)

    # Check if NumPyClient is returend
    if isinstance(client, NumPyClient):
        client = client.to_client()
        log(
            WARN,
            "Deprecation Warning: The `client_fn` function must return an instance "
            "of `Client`, but an instance of `NumpyClient` was returned. "
            "Please use `NumPyClient.to_client()` method to convert it to `Client`.",
        )

    message_type = message.metadata.message_type

    # Handle GetPropertiesIns
    if message_type == MessageTypeLegacy.GET_PROPERTIES:
        get_properties_res = maybe_call_get_properties(
            client=client,
            get_properties_ins=recordset_to_getpropertiesins(message.content),
        )
        out_recordset = getpropertiesres_to_recordset(get_properties_res)
    # Handle GetParametersIns
    elif message_type == MessageTypeLegacy.GET_PARAMETERS:
        get_parameters_res = maybe_call_get_parameters(
            client=client,
            get_parameters_ins=recordset_to_getparametersins(message.content),
        )
        out_recordset = getparametersres_to_recordset(
            get_parameters_res, keep_input=False
        )
    # Handle FitIns
    elif message_type == MessageType.TRAIN:
        fit_res = maybe_call_fit(
            client=client,
            fit_ins=recordset_to_fitins(message.content, keep_input=True),
        )
        out_recordset = fitres_to_recordset(fit_res, keep_input=False)
    # Handle EvaluateIns
    elif message_type == MessageType.EVALUATE:
        evaluate_res = maybe_call_evaluate(
            client=client,
            evaluate_ins=recordset_to_evaluateins(message.content, keep_input=True),
        )
        out_recordset = evaluateres_to_recordset(evaluate_res)
    else:
        raise ValueError(f"Invalid message type: {message_type}")

    # Return Message
    return message.create_reply(out_recordset)