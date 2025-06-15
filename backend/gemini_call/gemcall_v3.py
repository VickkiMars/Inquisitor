import asyncio
import time
import os
from collections import deque
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser # Assuming StrOutputParser is a common choice, replace with your actual parser
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import google.api_core.exceptions

load_dotenv()

# --- Rate Limiting Constants ---
MAX_REQUESTS_PER_MINUTE = 15
# Calculate the minimum delay required between initiating requests
MIN_DELAY_BETWEEN_REQUESTS_SECONDS = 60 / MAX_REQUESTS_PER_MINUTE # Result: 4.0 seconds

# Max concurrent generations: Limits how many API calls are in flight at any given moment.
# This should be less than or equal to MAX_REQUESTS_PER_MINUTE. A smaller number is often safer.
MAX_CONCURRENT_GENERATIONS = 3 # Adjust based on testing and stability needs

# --- Tenacity Retry Configuration for individual LLM invocations ---
@retry(
    stop=stop_after_attempt(3), # Reduced attempts for faster feedback on hard rate limits
    wait=wait_exponential(multiplier=1, min=2, max=5), # Shorter max wait for exponential backoff
    retry=retry_if_exception_type(google.api_core.exceptions.ResourceExhausted),
    reraise=True, # Re-raise the last exception if all retries fail
)
async def safe_invoke_llm(chain, input_data={}):
    """
    Asynchronously invokes an LLM chain with retry logic for ResourceExhausted errors.
    This function specifically uses `ainvoke` for asynchronous LangChain execution.
    """
    # LangChain chains use ainvoke for async calls
    return await chain.ainvoke(input_data)

# --- Main Rate-Limited Gemini Calling Function ---
async def call_gemini(prompts: list[str], parser):
    """
    Accepts a list of prompts and runs them against the Gemini API,
    enforcing a rate limit and concurrency limit.

    Args:
        prompts (list[str]): A list of string prompts to send to the LLM.
        parser: The LangChain output parser to apply to the model's output.

    Returns:
        list: A list of results from the successful prompt generations.
              Errors for individual prompts are logged.
    Raises:
        ValueError: If GOOGLE_API_KEY is not found.
        Exception: If all prompts fail or a critical unexpected error occurs.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables. Please set it.")

    # Initialize the Gemini model
    model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key)

    # Semaphore to control the number of concurrently running API calls
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_GENERATIONS)

    # Deque to store the timestamps of the last few API call initiations.
    # Used to ensure the rate limit is adhered to by spacing out requests.
    # We only need to track the time of the Nth-to-last call to ensure the rate.
    # For 15 req/min, we essentially need to ensure 4 seconds pass between starts.
    # A simple last_call_time is often sufficient, but a deque gives more robust window tracking.
    call_timestamps = deque()

    async def generate_single_prompt(prompt_text: str, prompt_index: int):
        """
        Generates a single prompt's response with rate limiting and concurrency control.
        """
        nonlocal call_timestamps # Allow modification of the outer scope's deque

        async with semaphore:
            # --- Rate Limiting Logic ---
            current_time = time.monotonic() # Get current time (monotonic for consistent delays)

            # Clean up old timestamps (only keep those within the last minute or relevant window)
            # This is more robust for long-running queues than just `last_call_time`
            while call_timestamps and call_timestamps[0] <= current_time - 60:
                call_timestamps.popleft()

            # If we've made too many requests in the last minute based on the deque, wait
            # (Though our simple `MIN_DELAY_BETWEEN_REQUESTS_SECONDS` is more direct for 15/min)
            # The more direct enforcement: Ensure minimum delay between *this* call and the *last* one
            if call_timestamps:
                time_since_last_call = current_time - call_timestamps[-1]
                if time_since_last_call < MIN_DELAY_BETWEEN_REQUESTS_SECONDS:
                    wait_time = MIN_DELAY_BETWEEN_REQUESTS_SECONDS - time_since_last_call
                    print(f"Rate limit enforced: Waiting for {wait_time:.2f} seconds before prompt {prompt_index}...")
                    await asyncio.sleep(wait_time)
            
            # Record the exact time this API call is about to be initiated
            start_invoke_time = time.monotonic()
            call_timestamps.append(start_invoke_time) # Add current initiation time

            print(f"[{time.strftime('%H:%M:%S', time.localtime(start_invoke_time))}] Initiating prompt {prompt_index}: '{prompt_text[:50]}...'")

            # Create an individual chain for this prompt
            chain = ChatPromptTemplate.from_template(prompt_text) | model | parser
            try:
                # Invoke the LLM asynchronously with retry logic
                result = await safe_invoke_llm(chain)
                print(f"[{time.strftime('%H:%M:%S')}] Completed prompt {prompt_index}.")
                return result
            except google.api_core.exceptions.ResourceExhausted as e:
                # This should be caught by tenacity, but if tenacity gives up, it's re-raised here
                print(f"[{time.strftime('%H:%M:%S')}] Rate limit exceeded for prompt {prompt_index}. Tenacity attempts exhausted. Error: {e}")
                raise e # Propagate the error for this specific prompt
            except Exception as e:
                # Catch any other exceptions during generation for this prompt
                print(f"[{time.strftime('%H:%M:%S')}] Error generating prompt {prompt_index}: {e}")
                raise e # Propagate the error

    # Create a list of coroutines (tasks) for all prompts
    # Each task will manage its own rate limiting and concurrency using the semaphore
    tasks = [
        generate_single_prompt(prompt_text, i)
        for i, prompt_text in enumerate(prompts)
    ]

    # Run all tasks concurrently, collecting results or exceptions
    # `return_exceptions=True` is vital: it ensures that if one prompt fails,
    # it doesn't stop the entire asyncio.gather, allowing other prompts to complete.
    all_results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results: separate successful outputs from errors
    successful_outputs = []
    errors = []
    for i, res in enumerate(all_results):
        if isinstance(res, Exception):
            # This is an exception object returned because of return_exceptions=True
            errors.append({"prompt_index": i, "error": str(res), "prompt_text": prompts[i]})
        else:
            successful_outputs.append(res)
    
    # Optional: Log a summary of results
    print(f"\n--- Generation Summary ---")
    print(f"Total prompts requested: {len(prompts)}")
    print(f"Successful generations: {len(successful_outputs)}")
    print(f"Failed generations: {len(errors)}")

    # Decide how to handle failures:
    # 1. Return only successful outputs and log errors (current behavior)
    # 2. Raise a custom exception if any errors occurred, listing them
    # 3. Return a tuple of (successful_outputs, errors) to the caller
    if errors:
        print("Details of failed prompts:")
        for error_detail in errors:
            print(f"  Prompt {error_detail['prompt_index']} (first 50 chars): '{error_detail['prompt_text'][:50]}...' Error: {error_detail['error']}")
        # If all prompts failed, you might want to raise a more general error
        if not successful_outputs:
            raise Exception(f"All {len(prompts)} prompts failed during generation. See logs for details.")

    return successful_outputs # Return only the successfully generated content

# --- Example Usage (How you would run this function) ---
async def main():
    # Example parser (replace with your actual parser if different from StrOutputParser)
    # Ensure your parser has an async parse method if it's not a simple StrOutputParser
    # For `StrOutputParser`, `aparse` is available if needed.
    parser = StrOutputParser()

    # Create a list of dummy prompts for demonstration
    test_prompts = [f"Generate a unique, short phrase for test {i+1}." for i in range(20)] # 20 prompts for testing rate limit

    print(f"Starting generation of {len(test_prompts)} prompts with rate limiting...")
    start_time = time.monotonic()

    try:
        results = await call_gemini(test_prompts, parser)
        end_time = time.monotonic()
        print("\n--- All Generations Completed ---")
        print(f"Total time taken: {end_time - start_time:.2f} seconds")
        print(f"Successfully generated {len(results)} results.")
        # for i, res in enumerate(results):
        #     print(f"Result {i+1}: {res[:100]}...")
    except Exception as e:
        end_time = time.monotonic()
        print(f"\n--- Generation Interrupted by Error ---")
        print(f"Total time before interruption: {end_time - start_time:.2f} seconds")
        print(f"Error: {e}")

# To run this script:
# if __name__ == "__main__":
#     # You need to import asyncio and run the main async function
#     # Make sure your GOOGLE_API_KEY is set in your .env file
#     asyncio.run(main())
