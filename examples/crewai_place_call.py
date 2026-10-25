"""CrewAI agent with Callin.io phone tools. pip install "callin[crewai]" """
from crewai import Agent, Task, Crew
from callin.crewai import CallinPlaceCallTool, CallinGetCallResultTool

caller = Agent(role="Phone assistant", goal="Get things done over the phone",
               backstory="You call businesses on behalf of the user and report back.",
               tools=[CallinPlaceCallTool(), CallinGetCallResultTool()])
task = Task(description="Call +34911234567 (in Spanish) and ask the clinic for the first available appointment next week.",
            expected_output="The appointment options offered", agent=caller)
print(Crew(agents=[caller], tasks=[task]).kickoff())
