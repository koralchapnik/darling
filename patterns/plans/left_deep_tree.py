from patterns.pattern import Pattern
from patterns.plans.plan import Plan


class LeftDeepTree(Plan):
    def __init__(self, spec: str):
        self.root = self._build_tree_from_spec(spec)

    def _build_plan_from_spec(self, spec: str) -> Pattern:
        pass

