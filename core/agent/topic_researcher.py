from crewai import Agent, Task, Crew, Process, LLM
from crewai_tools import SerperDevTool
import os

#gemini/gemini-2.0-flash-exp
llm = LLM(model="gemini/gemini-2.0-flash-thinking-exp-1219", temperature=0.7,api_key=os.environ["GEMINI_API_KEY"])
#llm = LLM(model="gpt-4o-mini", temperature=0.7,api_key="")

# Agent defination
researcher = Agent(
    role="{topic}  Senior Researcher",
    goal="Uncover groundbreaking techonologies in {topic} for year 2024",
    backstory="Driven by curiosity, you explore and share the latest innovations.",
    tools=[SerperDevTool()],
    llm=llm
)


research = Task(
    description="Identity the next big trend in {topic} with pros and cons.",
    expected_output=" A 3-paragraph report on emerging {topic} technologies",
    agent=researcher
)

def main():
    crew = Crew(
        agents=[researcher],
        tasks=[research],
        process=Process.sequential,
        verbose=True
    )

    result = crew.kickoff(inputs={'topic':'Agentic AI'})
    print(result)



if __name__ == "__main__":
    main()