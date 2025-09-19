from collections.abc import Sequence

from typing import Optional, TypeVar, Union, Literal

from datetime import datetime, timedelta

T = TypeVar('T')
ObjectOrSequence = Union[T, Sequence[T]]
StringOrSequence = Union[T, Sequence[T]]

Numeric = Union[float, int]

DateTimeExpression = Union[datetime, timedelta]

SymmetricalAlgorithmType = Literal[
        "HS256",]

AsymmetricalAlgorithmType = Literal[
        "RS256",
        ]

AlgorithmType = Union[SymmetricalAlgorithmType, AsymmetricalAlgorithmType]

TokenType = Literal['access', 'refresh']
TokenLocation = Literal['headers', 'cookies', 'json', 'query']
TokenLocations = Sequence[TokenLocation]

SameSitePolicy = Literal['lax', 'strict', 'none']
