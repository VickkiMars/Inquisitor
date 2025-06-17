from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import LLMChain
import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import google.api_core.exceptions  # for identifying rate limit errors
import time
load_dotenv()

# Retry configuration: retries up to 5 times with exponential backoff
@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(google.api_core.exceptions.ResourceExhausted),
    reraise=True,
)
def safe_invoke(chain):
    return chain.invoke({})  # Empty input since prompts are self-contained

def call_gemini(prompts, parser):
    api_key = os.getenv("GEMINI_API_KEY")
    model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key)

    parallel_chain = {
        f"prompt_{i}": (ChatPromptTemplate.from_template(prompt)) | model | parser
        for i, prompt in enumerate(prompts)
    }

    full_parallel = RunnableParallel(parallel_chain)

    try:
        result = safe_invoke(full_parallel)
    except google.api_core.exceptions.ResourceExhausted as e:
        print("Rate limit exceeded. Try again later.")
        raise e

    results = {f"prompt_{i}": result[f"prompt_{i}"] for i, _ in enumerate(prompts)}
    time.sleep(0.6)
    return list(results.values())
