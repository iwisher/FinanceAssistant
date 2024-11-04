from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import (
    ScrapeWebsiteTool,
    SerperDevTool,
    FileReadTool,
    DirectoryReadTool,
)
# from crewai.agent import CacheHandler

# Uncomment the following line to use an example of a custom tool
# from daily_summary.tools.custom_tool import MyCustomTool

# Check our tools documentations for more information on how to use them
# from crewai_tools import SerperDevTool

search_tool = SerperDevTool()
scrape_tool = ScrapeWebsiteTool()

directory_read_tool = DirectoryReadTool(directory="/home/rsong/DevSpace/wiseflow/download/news")
file_read_tool = FileReadTool()#'/home/rsong/DevSpace/wiseflow/download/news/ltshijie-20241102-1521.txt')


@CrewBase
class DailySummaryCrew:
    """DailySummary crew"""

    @agent
    def economist(self) -> Agent:
        return Agent(
            config=self.agents_config["economist"],
            # tools=[MyCustomTool()], # Example of custom tool, loaded on the beginning of file
            verbose=True,
            memory=True,
            allow_delegation=True,
            llm='gemini/gemini-1.5-flash-002'
        )

    @agent
    def political_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["political_analyst"],
            verbose=True,
            memory=True,
            allow_delegation=True,
            llm='gemini/gemini-1.5-flash-002'
        )

    @agent
    def stock_strategist(self) -> Agent:
        return Agent(
            config=self.agents_config["stock_strategist"],
            verbose=True,
            memory=True,
            allow_delegation=True,
            allow_code_execution=False,
            llm='gemini/gemini-1.5-flash-002'
        )

    @agent
    def risk_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["risk_analyst"],
            verbose=True,
            memory=True,
            allow_delegation=False,
            allow_code_execution=False,
            llm='gemini/gemini-1.5-flash-002'
        )

    @agent
    def news_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["news_analyst"],
            verbose=True,
            allow_delegation=True,
            allow_code_execution=False,
            # cache=True,
            # cache_handler=CacheHandler(),
            memory=True,
            tools=[directory_read_tool,file_read_tool,search_tool,scrape_tool],
            llm='gemini/gemini-1.5-flash-002'
        )

    @agent
    def critical_thinker(self) -> Agent:
        return Agent(
            config=self.agents_config["critical_thinker"],
            verbose=True,
            memory=True,
            allow_delegation=False,
            allow_code_execution=False,
            tools=[search_tool,scrape_tool],
            llm='gemini/gemini-1.5-flash-002'
        )

    @task
    def read_news_task(self) -> Task:
        return Task(
            config=self.tasks_config["read_news_task"],
            output_file="news_report.md"
        )

    @task
    def economic_analyze_task(self) -> Task:
        return Task(config=self.tasks_config["economic_analyze_task"], 
                    context=[self.read_news_task()],
                    output_file="economic_report.md")
        
    @task
    def political_analyze_task(self) -> Task:
        return Task(config=self.tasks_config["political_analyze_task"],
                    context=[self.read_news_task()],
                    output_file="political_report.md"
                    )

    @crew
    def crew(self) -> Crew:
        """Creates the DailySummary crew"""
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )


if __name__ == "__main__":
    """
    Run the crew.
    """
    inputs = {
    }
    DailySummaryCrew().crew().kickoff(inputs=inputs)