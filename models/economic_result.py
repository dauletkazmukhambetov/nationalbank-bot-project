from dataclasses import dataclass


@dataclass
class EconomicResult:

    trend: str

    summary: str

    last_value: float

    previous_value: float

    percent_change: float

    total_percent_change: float

    average_value: float