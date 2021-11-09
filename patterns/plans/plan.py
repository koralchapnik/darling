from abc import abstractmethod


class Plan:
    @abstractmethod
    def _build_plan_from_spec(self, spec: str):
        pass
