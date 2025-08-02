from typing import List

def generate_for_topic(n:int, difficulty:str, topic:str) ->str:
    mapping = {
        "beginner": "High School Certificate (HSC)",
        "intermediate": "International General Certificate of Secondary Education (IGCSE)",
        "advanced": "International Baccalaureate (IB) Diploma Programme",
        "expert": "Graduate Record Examination"
    }
    PROMPT = f"""
    Create {n} multiple choice or true/false questions with {mapping[difficulty]} difficulty based on the following topic {topic}.

    The structure of the mcq and true false question is as follows:

    {{
            "type": "multiple_choice",
            "question": "What is the capital of France?",
            "options": ["Berlin", "Paris", "Rome", "Madrid"],
            "answer": "Paris",
            "explanation": "Paris is the capital city of France, known for landmarks like the Eiffel Tower"
        }}

    {{
            "type": "true_false",
            "question": "The boiling point of water is 100°C at sea level.",
            "answer": "true",
            "explanation": "At standard atmospheric pressure (sea level), water boils at 100°C."
        }}


    """

def generate_question_type(context: str) -> str:
    PROMPT = f"""
    You are an expert question analyzer.

    Objective:
    You are provided with the following content: "{context}". 
    Your task is to outline three question types that are most suitable for the given content and return them in a python list.

    Select the two question types from the following question types:
        Multiple Choice Questions:
            - Questions with one correct answer and four wrong answers.

        Short Answer Questions:
            - Questions that require concise responses that capture key information from the content.

        Long Answer Question:
            - Questions that require detailed structured responses.

        Solve-Type Questions:
            - Questions that present a problem or scenario

        Fill-in-the-blank Questions:
            - Sentences or statements with missing words or phrases that must be completed

        Use-Case Questions:
            - Questions that place the topic into a real-world context.

        Matching type Questions:
            - Questions where learners match terms to their correct definitions.

        True/False Questions:
            - Questions that quickly test basic understanding or common misconceptions.

        Reverse Definition Questions:
            - Questions where a definition is provided and learners must identify the corresponding concept.

        Ordering type Questions:
            - Questions where a sequence of steps or events is provided and learners must correctly order the steps or events in their proper order.

        Respond with any of the following.
        - "multiple_choice"
        - "short_answer"
        - "long_answer"
        - "solve_type"
        - "fill_in_the_blank"
        - "use_case"
        - "matching"
        - "true_false"
        - "reverse_definition"
        - "ordering"

    Example output: 
    ["multiple_choice", "reverse_definition", "short_answer"]
    ["fill_in_the_blank", "multiple_choice", "use_case"]
    ["solve_type", "ordering", "long_answer"]

    Return only a list containing the question types, no extra jargon.
    """
    return PROMPT

def map_type_to_prompt(types: list) -> str:
    maps = {
        "multiple_choice": """Multiple-Choice-Questions (MCQ's):
        - Formulate questions with one correct answer and 4 distractors (incorrect options).
        - Ensure that the options are plausible and that the correct answer is supported by the content.
        - Include a brief explanation for the correct answer

        Example:
        {{
            "type": "multiple_choice",
            "question": "What is the capital of France?",
            "options": ["Berlin", "Paris", "Rome", "Madrid"],
            "answer": "Paris",
            "explanation": "Paris is the capital city of France, known for landmarks like the Eiffel Tower"
        }}
        """,

        "short_answer": """
        Short answer questions:
        - Ask for concise responses that capture key information from the content
        - These questions should require the respondent to recall or explain important facts or definitions briefly.

        Example:
        {{
            "type": "short_answer",
            "question": "Define Newton's First Law of Motion.",
            "answer": "An object at rest stays at rest and an object in motion stays in motion unless acted upon by an external force."
            "explanation": "This law highlights the concept of inertia and explains that motion doesn't change without a net external force"        
        }}

        """,

        "long_answer": """
        Long Answer Questions / Essay-Style Questions:
        - Formulate questions that prompt a detailed structured response.
        - Encourage critical thinking, synthesis of ideas, and in-depth discussion of the topic.
        - These should be open-ended and might involve comparing, contrasting or evaluating different aspects of the content.

        Example:
        {{
            "type": "long_answer",
            "question": "Discuss the causes and consequences of World War I."
            "answer": "Key causes include militarism, alliances, imperialism, and nationalism. The consequences included political restructuring, economic strain, and the Treaty of Versailles."
            "explanation" : "These points provide a comprehensive understanding of the root causes and widespread effects of WWI on global history."
        }}
        
        """,

        "solve_type": """
        4. Solve-Type / Problem-Solving Questions:
        - Create questions that present a problem or scenario which requires step-by-step reasoning.
        - In subjects such as mathematics, engineering or science, include calculations or procedural steps.
        - The question should require the use of methods or formulas discussed in the content.

        Example:
        {{
            "type": "solve_problem",
            "question": "Solve for x: 2x + 3 = 11",
            "answer": "x = 4",
            "explanation": "Subtracting 3 from both sides gives 2x = 8 then dividing both sides by 2 gives x = 4."
        }}

        """,

        "fill_in_the_blank": """
        5. Fill-in-the-blank Questions:
        - Design sentences or statements with missing words or phrases that need to be completed.
        - The blanks should be key concepts or terms from the content
        - Ensure that there is a clear unambiguous answer for each blank

        Example:
        {{
            "type": "fill_in_the_blank",
            "question": The process by which plants make food using sunlight is called _____.",
            "answer": "Photosynthesis",
            "explanation": "Photosynthesis is the process where plants use sunlight, carbon dioxide, and water to produce glucose and oxygen."    
        }}

        """,

        "use_case": """
        6. Use-Case / Scenario-Based Questions:
        - Develop questions that place the topic in a real-world context.
        - The questions should illustrate practical applications or decision-making based on the content.
        - Encourage the application of theoretical knowledge in realistic settings.

        Example:
        {{
            "type": "use_case",
            "question" "A company wants to imporove customer engagement through automation. Suggest a suitable AI technique and explain how it would help.",
            "answer": "Using chatbots powered by Natural Language Processing can help automate customer service and improve response time.",
            "explanation": "Chatbots use NLP to interpret customer queries and provide instant response, reducing human workload and improving service efficiency."
        }}

        """,

        "matching": """
        Matching Type Questions:
        - Create questions where learners match terms to their corresponding closely related concepts or definitions
        - Present a list of terms alongside a separate list of definitions or closely related concepts
        - Ask learners to correctly associate each term with its matching definition or closely related concept

        Example:
        {{
            "type": "matching",
            "question": "Match the scientific terms with their correct definitions.",
            "pairs": {{
                "Osmosis": "The diffusion of water across a semipermeable membrane.",
                "Photosynthesis": "The process by which green plants use sunlight to synthesize food.",
                "Mitochondria": "The powerhouse of the cell, responsible for energy production."
            }},
            "explanation": "Each term matches a distinct biological function or process essential to cellular activity."
        }}

        """,

        "true_false": """
        True / False Questions
        - Develop questions that quickly test basic understanding or common misconceptions.
        - Each statement should be clearly either True or False based on the content.
        - Add explanations for the correct classification where necessary

        Example:
        {{
            "type": "true_false",
            "question": "The boiling point of water is 100°C at sea level.",
            "answer": "true",
            "explanation": "At standard atmospheric pressure (sea level), water boils at 100°C."
        }}

        """,

        "reverse_definition": """
        Reverse Definition Questions:
        - Curate definitions where a definition is provided and learners must identify the corresponding concept.
        - Focus on ensuring the definition clearly points to one specific concept
        - This format reinforces the connection between terminology and its meaning.

        Example:
        {{
            "type": "reverse_definition",
            "question": "A gas law stating that pressure and volume are inversely proportional at constant temperature.",
            "answer": "Boyle's Law",
            "explanation": "Boyle's Law describes the inverse relationship between the pressure and volume of a gas at constant temperature.",
        }}

        """,

        "ordering": """
        10. Ordering-type Questions:
        - Create a sequence of steps or events alongside their order.
        - Ask learners to correctly order the steps or events in their proper order.

        Example:
        {{
            "type": "ordering",
            "question": "Arrange the steps of the water cycle in the correct order.",
            "items": [
                "Condensation",
                "Precipitation",
                "Evaporation",
                "Collection"
            ],
            "correct_order":[
                "Evaporation",
                "Condensation",
                "Precipitation",
                "Collection"
            ],
            "explanation": "The water cycle begins with evaporation of water from surfaces, followed by condensation in the atmosphere to form clouds, then precipitation as rain or snow, and finally collection in water bodies of water like rivers and lakes."
        }}

        """
    }
    out = ""
    for x in types:
        out += f"""{maps[x]}
    
    """
    return out

def generate_prompt(chunk:str, prompt_types: str) -> str:
    """
    Generates questions based on the input chunk of text
    
    Args:
        chunk (str): The text chunk from which to generate questions
        prompt_types: The question types to be generated

    Returns:
        A list of questions.
    """
    PROMPT = f"""
    You are an expert question generator, generating questions for the next generation of students, the quality of the student will be dependent on the quality of your questions, how thorughly you drill the student will reflect in the future.

    Objective:
    You are provided with {chunk}. Your task is to generate 1 question per question type that assesses understanding, application, analysis, and synthesis of the content. 
    The output must include, and is limited to, the following Question Types, make sure to strictly follow the question formats found in Question Types:

    Question Types:
    [{prompt_types}]


    Instructions:
    - Input Interpretation:
        Carefully analyze the provided content or topic. Identify key concepts, definitions, procedures, and applications.

    - Question Types:
        The following are the allowed question types: 
        - "multiple_choice"
        - "short_answer"
        - "long_answer"
        - "solve_type"
        - "fill_in_the_blank"
        - "use_case"
        - "matching"
        - "true_false"
        - "reverse_definition"
        - "ordering"

    DO NOT USE ANY ALTERNATIVE QUESTION TYPES
    - Question Categorization:
        Divide the content into logical segments or themes if applicable. Ensure you generate at one question per question type.

    - Quality and Clarity:
        Make sure every question is clearly worded and unambiguous. Avoid overly complex language unless the content itself is technical, and always provide necessary context to prevent confusion.

    - Review and Variation:
        Ensure a balanced mix of question difficulties ranging form basic recall to higher-order analysis and verify that each question directly relates to the content. The goal is to challenge learners comprehensively across all aspects of the material

    - Explanation:
        Your explanation should contain a valid explanation of the answer, not a description of why that is the answer.

    - Relevant output:
        Do not create any additional question types: AVOID ANY JARGON in your response, respond ONLY with the questions in PYTHON DICTIONARY structure/format.

    - Respond:
        RESPOND WITH THE QUESTIONS IN THE SPECIFIED FORMAT
    """
    return PROMPT