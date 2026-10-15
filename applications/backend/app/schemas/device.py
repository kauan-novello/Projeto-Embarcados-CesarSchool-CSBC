from datetime import datetime

from pydantic import BaseModel, computed_field


class DeviceOut(BaseModel):
    id: str
    last_seen_at: datetime

    @computed_field  # type: ignore[prop-decorator]
    @property
    def label(self) -> str:
        return f"SolarSense-{self.id[-4:]}"

    model_config = {"from_attributes": True}


class DeviceLinkIn(BaseModel):
    device_id: str
