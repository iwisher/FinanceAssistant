import dspy
import os

import dspy.evaluate
api_key = os.environ.get("GEMINI_KEY","")
#lm = dspy.LM('gemini/gemini-2.0-flash',api_key=api_key) #-thinking-exp-01-21
lm = dspy.LM('ollama/deepseek-r1:14b',  api_base="http://localhost:11434")
dspy.configure(lm=lm)

print('here')

math = dspy.ChainOfThought("question -> answer: float")
math(question = "Two dice are tossed. What is the probliaity that the sume equals two?")



from dspy.datasets import HotPotQA

def search_wikipedia(query:str) -> list[str]:
    results = dspy.ColBERTv2(url='http://20.102.90.50:2017/wiki17_abstracts')(query, k=3)
    return [x['text'] for x in results]


trainset = [x.with_inputs('question') for x in HotPotQA(train_seed=2024, train_size=50).train]

react = dspy.ReAct("question -> answer", tools=[search_wikipedia])


tp = dspy.MIPROv2(metric=dspy.evaluate.answer_exact_match, auto="light", num_threads=10)

optimzed_react = tp.compile(react, trainset=trainset)

print (optimzed_react)