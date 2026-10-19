from __future__ import annotations

from pulsar.promotion.machine import PromotionMachine, PromotionRecord


class Validator:
    """Runs the gauntlet. Cannot place orders or change risk limits."""

    name = "validator"
    tools = ("run_gauntlet",)

    def __init__(self, machine: PromotionMachine) -> None:
        self.machine = machine

    def run_gauntlet(self, **kwargs) -> list[PromotionRecord]:
        return self.machine.run_cycle(**kwargs)
