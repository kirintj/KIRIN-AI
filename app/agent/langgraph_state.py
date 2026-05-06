from langgraph.graph import MessagesState


class JobAssistantState(MessagesState):
    query: str = ""
    intent: str = ""
    tool_name: str = ""
    tool_args: dict = {}
    tool_output: str = ""
    iteration: int = 0
    max_iterations: int = 3
    need_more: bool = False
    final_answer: str = ""
    user_id: str = "default"
    use_llm_router: bool = False
