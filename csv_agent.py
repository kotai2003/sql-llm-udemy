from langchain_core.messages import HumanMessage, SystemMessage
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import pandas as pd

# load environment variables from .env file
load_dotenv()

openai_key = os.getenv("OPENAI_API_KEY")

# llm_name = "gpt-4.1-mini"
llm_name = "gpt-4.1"
model = ChatOpenAI(model_name=llm_name, openai_api_key=openai_key, temperature=0)

#read csv file
df = pd.read_csv('./data/salaries_2023.csv').fillna(value=0)

#print(df.head())

from langchain_experimental.agents import (
    create_pandas_dataframe_agent,
    create_csv_agent
    )

agent  = create_pandas_dataframe_agent(
                    llm=model, 
                    df=df,
                    verbose=True,
                    allow_dangerous_code=True
                                )

# response = agent.invoke("how many rows are there in the dataset?")

# print(response)

# then let's add some pre and suffix prompt
CSV_PROMPT_PREFIX = """
First set the pandas display options to show all the columns,
get the column names and then answer the quesiton.
"""

CSV_PROMPT_SUFFIX = """
- **ALWAYS** before giving the Final Answer, try another method.
Then reflect on the answers of the two methods you did and ask yourself
if it answers correctly the original question.
If you are not sure, try another method.
FORMAT 4 FIGURES OR MORE WITH COMMAS.
- If the methods tried do not give the same result,reflect and
try again until you have two methods that have the same result.
- If you still cannot arrive to a consistent result, say that
you are not sure of the answer.
- If you are sure of the correct answer, create a beautiful
and thorough response using Markdown.
- **DO NOT MAKE UP AN ANSWER OR USE PRIOR KNOWLEDGE,
ONLY USE THE RESULTS OF THE CALCULATIONS YOU HAVE DONE**.
- **ALWAYS**, as part of your "Final Answer", explain how you got
to the answer on a section that starts with: "\n\nExplanation:\n".
In the explanation, mention the column names that you used to get
to the final answer.
"""

QUESTION = "Which grade has the highest average base salary, and compare the average female pay vs male pay?"

# res = agent.invoke(CSV_PROMPT_PREFIX + QUESTION + CSV_PROMPT_SUFFIX)

# print(f"Final result: {res["output"]}")

import streamlit as st

st.title("Database AI Agent with LangChain and OpenAI")
st.write("### Dataset Preview")
st.write(df.head())

# User input for questions
st.write("### Ask a question about the dataset")
user_question = st.text_input("Enter your question here:", value=QUESTION)

# Run the agent when the user submits a question
if st.button("Get Answer"):
    if user_question:
        response = agent.invoke(CSV_PROMPT_PREFIX + user_question + CSV_PROMPT_SUFFIX)
        st.write("### Answer:")
        st.markdown(response["output"])
    else:
        st.write("Please enter a question.")