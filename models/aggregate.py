
from typing import Dict, Optional
from pydantic import BaseModel


class SimpleAggregate(BaseModel):
    collection: str
    groupBy: str
    grouping: Dict[str,str]
    skip: Optional[int] = None
    limit: Optional[int] = None

    