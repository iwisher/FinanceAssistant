import dspy
import os

import dspy.evaluate
api_key = os.environ.get("GEMINI_KEY","")
#lm = dspy.LM('gemini/gemini-2.0-flash',api_key=api_key) #-thinking-exp-01-21
lm = dspy.LM('ollama/deepseek-r1:14b',  api_base="http://localhost:11434")
dspy.configure(lm=lm)


# res = lm("Say this is a test!", temperature=0.7)
# print(res)
# res = lm(messages=[{"role":"user","content":"Don't think, and just say this is a test!"}])
# print(f'With message:\n {res}')


# Define a module (ChainOfThought) and assign it a signature (return an answer, given a question).
qa = dspy.ChainOfThought('question -> answer')

# Run with the default LM configured with `dspy.configure` above.
response = qa(question="How many floors are in the castle David Gregory inherited?")

print(f'History:\n {lm.history}')


print(response.answer)