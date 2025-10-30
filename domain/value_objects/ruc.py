from decimal import Decimal

class RUC:
    def __init__(self, value: str):
        if not self._validate_ruc(value):
            raise ValueError("RUC inválido")
        self.value = value

    def _validate_ruc(self, value: str) -> bool:
        if not value.isdigit() or len(value) != 13:
            return False
        # Simplified Ecuadorian RUC validation (example)
        coefficients = [2, 1, 2, 1, 2, 1, 2, 1, 2]
        digits = [int(d) for d in value[:9]]
        check_digit = int(value[9])
        total = sum(c * d for c, d in zip(coefficients, digits))
        mod = total % 11
        expected = 11 - mod if mod != 0 else 0
        return check_digit == expected

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other) -> bool:
        if not isinstance(other, RUC):
            return False
        return self.value == other.value