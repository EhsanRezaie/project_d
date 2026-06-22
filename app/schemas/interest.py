from uuid import UUID
from typing import Optional
from pydantic import BaseModel
 
 
class InterestResponse(BaseModel):
    """A single interest, as returned to the client.
 
    `name` is a stable English key (e.g. 'football'), NOT display text —
    Flutter resolves it to a localized label client-side. See
    app/db/seed_data/interests.json for the full seeded set.
    """
    id: UUID
    name: str
    category: Optional[str] = None
    icon: Optional[str] = None
 
    class Config:
        from_attributes = True