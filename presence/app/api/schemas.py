from uuid import UUID

from pydantic import BaseModel, Field


class ConnectionCreateRequest(BaseModel):
    connection_id: str
    user_id: UUID


class SubscriptionUpdateRequest(BaseModel):
    add: list[UUID] = Field(default_factory=list)
    remove: list[UUID] = Field(default_factory=list)


class UserStatusItem(BaseModel):
    user_id: UUID
    online: bool


class SubscriptionsResponse(BaseModel):
    statuses: list[UserStatusItem]
