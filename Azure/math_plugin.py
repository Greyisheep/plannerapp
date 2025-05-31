import logging
from typing import Annotated

from semantic_kernel.functions.kernel_function_decorator import kernel_function

logger = logging.getLogger(__name__)

class MathPlugin:
    """A plugin to solve basic math expressions."""

    @kernel_function(
        description="Solves a basic math expression like '5 + 3'.",
        name="solve_math_expression"
    )
    def solve(
        self, 
        expression: Annotated[str, "The mathematical expression to solve (e.g., '2 + 2', '5 * 3 / 2')."]
    ) -> Annotated[str, "The result of the math expression, or an error message."]:
        """Solves a math expression.

        Args:
            expression: The mathematical expression to solve.

        Returns:
            The result of the expression or an error message if solving fails.
        """
        logger.info(f"Solving math expression: {expression}")
        try:
            # WARNING: eval can be dangerous if the input is not sanitized.
            # For a production app, consider using a safer math expression parser/evaluator.
            # Example: ast.literal_eval for very simple expressions, or a dedicated library.
            # For this example, we'll use eval for simplicity, assuming trusted input
            # or that the LLM will provide safe expressions.
            result = eval(expression)
            logger.info(f"Math expression result: {result}")
            return f"{expression} = {result}"
        except Exception as e:
            logger.error(f"Error solving expression '{expression}': {e}")
            return f"Could not solve: {expression}. Error: {e}"

# Example usage (for testing the plugin directly):
if __name__ == "__main__":
    solver = MathPlugin()
    problem = "(5 + 3) * 2 / 4 - 1"
    solution = solver.solve(problem)
    print(f"Solution for '{problem}': {solution}")

    problem_invalid = "5 + abc"
    solution_invalid = solver.solve(problem_invalid)
    print(f"Solution for '{problem_invalid}': {solution_invalid}") 