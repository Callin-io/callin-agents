"""pip install callin ; env CALLIN_API_KEY, CALLIN_AGENT_ID"""
from callin import Callin

c = Callin()
result = c.place_call("+390111234567",
                      objective="Ask what time the shop closes today and whether they have running shoes size 42 in stock.",
                      language="it", wait=True)
print(result.status, result.summary)
