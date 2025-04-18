from pydantic import BaseModel, ConfigDict


class PackageTypeBase(BaseModel):
    name: str
    description: str | None = None


class PackageTypeCreate(PackageTypeBase):
    pass


class PackageTypeUpdate(PackageTypeBase):
    pass


class PackageTypeInDB(PackageTypeBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class PackageType(PackageTypeInDB):
    pass
