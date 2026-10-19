import math


class TruthTable:
    """truth table generator that accepts minterms as input
    and exports to Markdown or output terminal tables.
    """

    def __init__(
        self,
        minterms: list[int],
        num_vars: int | None = None,
        var_names: list[str] | None = None,
        output_name: str = "F",
    ):
        """
        minterms: List of minterm integers where output evaluates to 1.
        num_vars: Number of input variables. Auto-calculated if None.
        var_names: Custom names for input variables (e.g. ['A', 'B', 'C']).
        output_name: Name of the output column. Defaults to 'F'.
        """
        self.minterms = set(minterms)
        self.output_name = output_name

        # Handle variable naming and count
        if var_names is not None:
            self.var_names = var_names
            self.num_vars = len(var_names)
        elif num_vars is not None:
            self.num_vars = num_vars
            self.var_names = self._default_var_names(num_vars)
        else:
            max_m = max(self.minterms) if self.minterms else 0
            self.num_vars = max(1, math.ceil(math.log2(max_m + 1))) if max_m > 0 else 1
            self.var_names = self._default_var_names(self.num_vars)

        self.rows = self._generate_rows()

    @staticmethod
    def _default_var_names(num_vars: int) -> list[str]:
        """Generates ['A', 'B', 'C', ...] for <= 26 vars, else ['x0', 'x1', ...]."""
        if num_vars <= 26:
            return [chr(65 + i) for i in range(num_vars)]
        return [f"x{i}" for i in range(num_vars)]

    def _generate_rows(self) -> list[dict[str, int]]:
        """constructs 2^N rows for the truth table"""
        table = []
        total_rows = 1 << self.num_vars  # 2^num_vars

        for i in range(total_rows):
            row = {}
            for bit_idx, name in enumerate(self.var_names):
                shift = self.num_vars - 1 - bit_idx
                row[name] = (i >> shift) & 1

            row[self.output_name] = 1 if i in self.minterms else 0
            table.append(row)

        return table

    def to_markdown(self) -> str:
        """returns the truth table formatted for Markdown"""
        headers = self.var_names + [self.output_name]
        header_line = "| " + " | ".join(headers) + " |"
        sep_line = "| " + " | ".join("---" for _ in headers) + " |"

        data_lines = [
            "| " + " | ".join(str(row[h]) for h in headers) + " |"
            for row in self.rows
        ]

        return "\n".join([header_line, sep_line] + data_lines)

    def to_cli(self, style: str = "ascii") -> str:
        """returns a formatted table for terminal
        args:
            style: 'ascii' (default) or 'unicode' for box-drawing characters.
        """
        headers = self.var_names + [self.output_name]
        widths = {h: max(len(h), 1) for h in headers}

        if style == "unicode":
            top = "┌─" + "─┬─".join("─" * widths[h] for h in headers) + "─┐"
            mid = "├─" + "─┼─".join("─" * widths[h] for h in headers) + "─┤"
            bot = "└─" + "─┴─".join("─" * widths[h] for h in headers) + "─┘"
            v = "│"
        else:
            border = "+" + "+".join("-" * (widths[h] + 2) for h in headers) + "+"
            top = mid = bot = border
            v = "|"

        lines = [top]

        # Header row
        h_cells = [f"{h:^{widths[h]}}" for h in headers]
        lines.append(f"{v} " + f" {v} ".join(h_cells) + f" {v}")
        lines.append(mid)

        # Data rows
        for row in self.rows:
            r_cells = [f"{row[h]:^{widths[h]}}" for h in headers]
            lines.append(f"{v} " + f" {v} ".join(r_cells) + f" {v}")

        lines.append(bot)
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.to_cli()

    def __repr__(self) -> str:
        return f"TruthTable(minterms={sorted(list(self.minterms))}, num_vars={self.num_vars})"


# # Example Use:
# tt = TruthTable(minterms=[0, 2, 5, 7])

# print(tt.to_cli(style="unicode"))
