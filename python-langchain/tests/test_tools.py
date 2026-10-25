from langchain_callin import CallinToolkit


class Fake:
    def list_conversations(self, page_size=10):
        return {"items": [], "page_size": page_size}


def test_toolkit_names():
    names = [t.name for t in CallinToolkit(client=Fake()).get_tools()]
    assert names == ["callin_place_call", "callin_get_call_result", "callin_list_recent_calls"]


def test_list_runs():
    tool = CallinToolkit(client=Fake()).get_tools()[2]
    assert '"page_size": 3' in tool.invoke({"limit": 3})
