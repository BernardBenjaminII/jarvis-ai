from __future__ import annotations


class StageRegistry:

    def __init__(self):

        self._stages = []

    def register(self, stage):

        self._stages.append(stage)

        self._stages.sort(key=lambda s: s.order)

    @property
    def stages(self):

        return list(self._stages)
