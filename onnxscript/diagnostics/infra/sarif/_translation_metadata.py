# DO NOT EDIT! This file was generated by jschema_to_python version 0.0.1.dev29,
# with extension for dataclasses and type annotation.

from __future__ import annotations

import dataclasses
from typing import Optional

from onnxscript.diagnostics.infra.sarif import (
    _multiformat_message_string,
    _property_bag,
)


@dataclasses.dataclass
class TranslationMetadata(object):
    """Provides additional metadata related to translation."""

    name: str = dataclasses.field(metadata={"schema_property_name": "name"})
    download_uri: Optional[str] = dataclasses.field(
        default=None, metadata={"schema_property_name": "downloadUri"}
    )
    full_description: Optional[
        _multiformat_message_string.MultiformatMessageString
    ] = dataclasses.field(default=None, metadata={"schema_property_name": "fullDescription"})
    full_name: Optional[str] = dataclasses.field(
        default=None, metadata={"schema_property_name": "fullName"}
    )
    information_uri: Optional[str] = dataclasses.field(
        default=None, metadata={"schema_property_name": "informationUri"}
    )
    properties: Optional[_property_bag.PropertyBag] = dataclasses.field(
        default=None, metadata={"schema_property_name": "properties"}
    )
    short_description: Optional[
        _multiformat_message_string.MultiformatMessageString
    ] = dataclasses.field(default=None, metadata={"schema_property_name": "shortDescription"})


# flake8: noqa
