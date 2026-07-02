from dataclasses import dataclass


@dataclass(frozen=True)
class CookingToolDefinition:
    id: str
    name: str
    prompt_name: str


COOKING_TOOLS: dict[str, CookingToolDefinition] = {
    "thermomix": CookingToolDefinition(
        id="thermomix",
        name="Thermomix",
        prompt_name="recipes.tool-thermomix",
    ),
    "pressure_cooker": CookingToolDefinition(
        id="pressure_cooker",
        name="Pressure Cooker",
        prompt_name="recipes.tool-pressure-cooker",
    ),
}


def get_tool(tool_id: str) -> CookingToolDefinition:
    tool = COOKING_TOOLS.get(tool_id)
    if not tool:
        raise ValueError(f"Unknown cooking tool: {tool_id}")
    return tool


def validate_tool_ids(tool_ids: list[str]) -> list[CookingToolDefinition]:
    return [get_tool(tid) for tid in tool_ids]
