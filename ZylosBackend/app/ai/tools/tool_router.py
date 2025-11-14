
"""
Tool router for Zylos.
Call style:
    from app.ai.tools.tool_router import call_tool
    res = call_tool("weather", city="Mumbai")
"""

from typing import Any
from . import weather, search, youtube, wikipedia, location, time_date, system_control

TOOLS = {
    "weather": weather.get_weather,
    "search": search.duckduck_search,
    "youtube": youtube.search_youtube,
    "wikipedia": wikipedia.get_summary,
    "location": location.get_current_city,
    "time_date": time_date.get_current_datetime,
    "system_control": system_control.run_command,
}

class ToolNotFound(Exception):
    pass

def call_tool(tool_name: str, *args, **kwargs) -> Any:
    fn = TOOLS.get(tool_name)
    if not fn:
        raise ToolNotFound(f"Tool '{tool_name}' not found")
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        # Bubble up or wrap error message (brain can handle fallback)
        return f"[tool_error] {tool_name}: {str(e)}"