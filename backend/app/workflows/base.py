from abc import ABC, abstractmethod
from typing import Any


class BaseStepHandler(ABC):
    @abstractmethod
    async def execute(self, config: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """
        Executes the workflow step.
        :param config: The specific configuration for this step.
        :param context: The dynamic context shared across steps in this execution.
        :return: A dictionary containing the step's execution output/result.
        """
        pass
