
from typing import Dict, Optional, Union
from pydantic import BaseModel


class SimpleAggregate(BaseModel):
    collection: str
    simple_filter: Dict[str, Union[str, float, int]]
    do_count: bool
    do_distinct: bool
    distinct_field: Optional[str] = None
    skip: Optional[int] = None
    limit: Optional[int] = None

    