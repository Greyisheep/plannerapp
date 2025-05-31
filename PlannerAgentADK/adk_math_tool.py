import logging

# ADK does not use @kernel_function, it infers from docstrings and type hints.
# However, for complex argument descriptions, the google.adk.tools.tool decorator can be used.
# For simplicity here, we'll rely on docstrings and standard type hints.

logger = logging.getLogger(__name__)

def solve_math_expression(
    expression: str
) -> str:
    """Solves a basic math expression like '5 + 3'.

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

# Example usage (for testing the tool directly):
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    problem = "(5 + 3) * 2 / 4 - 1"
    solution = solve_math_expression(problem)
    print(f"Solution for '{problem}': {solution}")

    problem_invalid = "5 + abc"
    solution_invalid = solve_math_expression(problem_invalid)
    print(f"Solution for '{problem_invalid}': {solution_invalid}") 