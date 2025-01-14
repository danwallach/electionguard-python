from datetime import datetime
from enum import IntEnum
from io import TextIOWrapper
import json
import os
from pathlib import Path
from typing import Any, List, Type, TypeVar, Union


from dacite import Config, from_dict
from dateutil import parser
from pydantic.json import pydantic_encoder
from pydantic.tools import schema_json_of


from .big_integer import BigInteger
from .ballot_box import BallotBoxState
from .group import ElementModP, ElementModQ
from .manifest import ElectionType, ReportingUnitType, VoteVariationType, SpecVersion
from .proof import ProofUsage
from .utils import BYTE_ENCODING, BYTE_ORDER, ContestErrorType


_PAD_BYTE = b"\x00"
PAD_INDICATOR_SIZE = 2

_T = TypeVar("_T")

_indent = 2
_file_extension = "json"

_config = Config(
    cast=[
        datetime,
        BigInteger,
        ContestErrorType,
        ElementModP,
        ElementModQ,
        ElectionType,
        BallotBoxState,
        ElectionType,
        ReportingUnitType,
        SpecVersion,
        VoteVariationType,
        ProofUsage,
    ],
    type_hooks={datetime: parser.parse},
)


class PaddedDataSize(IntEnum):
    """Define the sizes for padded data."""

    Bytes_512 = 512 - PAD_INDICATOR_SIZE


class TruncationError(ValueError):
    """A specific truncation error to indicate when padded data is truncated."""


def padded_encode(data: Any, size: PaddedDataSize) -> bytes:
    return _add_padding(to_raw(data).encode(BYTE_ENCODING), size)


def padded_decode(type_: Type[_T], padded_data: bytes, size: PaddedDataSize) -> _T:
    return from_raw(type_, _remove_padding(padded_data, size))


def _add_padding(
    message: bytes, size: PaddedDataSize, allow_truncation: bool = False
) -> bytes:
    """Add padding to message in bytes."""
    message_length = len(message)
    if message_length > size:
        if allow_truncation:
            message_length = size
        else:
            raise TruncationError(
                "Padded data exceeds allowed padded data size of {size}."
            )
    padding_length = size - message_length
    leading_byte = padding_length.to_bytes(PAD_INDICATOR_SIZE, byteorder=BYTE_ORDER)
    padded = leading_byte + message[:message_length] + _PAD_BYTE * padding_length
    return padded


def _remove_padding(padded: bytes, size: PaddedDataSize) -> bytes:
    """Remove padding from padded message in bytes."""

    padding_length = int.from_bytes(padded[:PAD_INDICATOR_SIZE], byteorder=BYTE_ORDER)
    message_end = size + PAD_INDICATOR_SIZE - padding_length
    return padded[PAD_INDICATOR_SIZE:message_end]


def construct_path(
    target_file_name: str,
    target_path: str = "",
    target_file_extension: str = _file_extension,
) -> str:
    """Construct path from file name, path, and extension."""

    target_file = f"{target_file_name}.{target_file_extension}"
    return os.path.join(target_path, target_file)


def from_raw(type_: Type[_T], raw: Union[str, bytes]) -> _T:
    """Deserialize raw json string as type."""

    return from_dict(type_, json.loads(raw), _config)


def to_raw(data: Any) -> str:
    """Serialize data to raw json format."""

    return json.dumps(data, indent=_indent, default=pydantic_encoder)


def from_file_wrapper(type_: Type[_T], file: TextIOWrapper) -> _T:
    """Deserialize json file as type."""

    data = json.load(file)
    return from_dict(type_, data, _config)


def from_file(type_: Type[_T], path: Union[str, Path]) -> _T:
    """Deserialize json file as type."""

    with open(path, "r", encoding=BYTE_ENCODING) as json_file:
        data = json.load(json_file)
    return from_dict(type_, data, _config)


def from_list_in_file(type_: Type[_T], path: Union[str, Path]) -> List[_T]:
    """Deserialize json file that has an array of certain type."""

    with open(path, "r", encoding=BYTE_ENCODING) as json_file:
        data = json.load(json_file)
        ls: List[_T] = []
        for item in data:
            ls.append(from_dict(type_, item, _config))
    return ls


def from_list_in_file_wrapper(type_: Type[_T], file: TextIOWrapper) -> List[_T]:
    """Deserialize json file that has an array of certain type."""

    data = json.load(file)
    ls: List[_T] = []
    for item in data:
        ls.append(from_dict(type_, item, _config))
    return ls


def to_file(
    data: Any,
    target_file_name: str,
    target_path: str = "",
) -> str:
    """Serialize object to JSON"""

    if not os.path.exists(target_path):
        os.makedirs(target_path)

    path = construct_path(target_file_name, target_path)
    with open(
        path,
        "w",
        encoding=BYTE_ENCODING,
    ) as outfile:
        json.dump(data, outfile, indent=_indent, default=pydantic_encoder)
        return path


def get_schema(_type: Any) -> str:
    """Get JSON Schema for type"""

    return schema_json_of(_type)
