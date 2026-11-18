from dataclasses import dataclass, field


@dataclass
class InMemoryWaitlistProvider:
    subscriptions: list[tuple[str, int]] = field(default_factory=list)

    def subscribe(self, email: str, list_id: int) -> None:
        self.subscriptions.append((email, list_id))
