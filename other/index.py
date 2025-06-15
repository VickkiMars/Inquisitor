from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv

load_dotenv()
def run_parallel_prompts():
    # Set your Google API key (better to use environment variables)
    api_key = os.getenv("GOOGLE_API_KEY")
    print(api_key)
    
    # Initialize the Gemini model
    model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key)
    
    prompts = []

    # Define and execute parallel prompts
    parallel_chain = RunnableParallel({
        "joke": (
            ChatPromptTemplate.from_template("Tell me a joke about space") 
            | model
        ),
        "summary": (
            ChatPromptTemplate.from_template("Give me a 1-sentence summary about space") 
            | model
        ),
        "facts": (
            ChatPromptTemplate.from_template("List three interesting facts about space") 
            | model
        )
    })
    
    # Invoke the parallel chain
    result = parallel_chain.invoke({})  # Empty input since prompts are self-contained
    
    # Return the results
    return {
        "joke": result["joke"].content,
        "summary": result["summary"].content,
        "facts": result["facts"].content
    }

# Execute and print results
if __name__ == "__main__":
    results = run_parallel_prompts()
    print("=== Joke ===")
    print(results["joke"])
    print("\n=== Summary ===")
    print(results["summary"])
    print("\n=== Facts ===")
    print(results["facts"])
