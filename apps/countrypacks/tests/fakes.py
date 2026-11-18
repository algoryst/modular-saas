from dataclasses import dataclass, field

from apps.countrypacks.base import CompanyRecord, RegistryUnavailable


@dataclass
class FakeCompanyRegistry:
    """In-memory CompanyRegistry for tests of anything that looks companies up."""

    records: dict[str, CompanyRecord] = field(default_factory=dict)
    down: bool = False

    def lookup(self, type_code: str, value: str) -> CompanyRecord | None:
        if self.down:
            raise RegistryUnavailable("fake registry is down")
        if type_code != "siret":
            return None
        return self.records.get(value.replace(" ", ""))
