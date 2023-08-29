import streamlit as st
import os
from dotenv import load_dotenv
import openai
from datetime import datetime
import tiktoken

def create_directories():
    # create log directory if it doesn't exist
    if not os.path.exists('log'):
        os.makedirs('log')
    # create prompts directory if it doesn't exist
    if not os.path.exists('prompts'):
        os.makedirs('prompts') 
        # create a base_prompts file if it doesn't exist
    path = "prompts/base_prompts"
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write("You are an expert researcher")
    
def num_tokens_from_string(string, model="gpt-3.5-turbo" ):
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.encoding_for_model(model)
    num_tokens = len(encoding.encode(string))
    return num_tokens

def send_message(message, model="gpt-3.5-turbo", temperature=0.7):
    print(model)
    try:
        result = openai.ChatCompletion.create(
            model=model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": message}
            ]
        )
        return result.choices[0].message.content
    except Exception as e:
        print(f"Error in send_message: {e}")
        return None


# calculate number of tokens remaining
def calculate_tokens_remaining(token_count: int, model: str) -> int:
    """
    Calculate the number of tokens remaining based on token count and model type.

    Args:
        token_count (int): The count of tokens.
        model (str): The type of model. Accepts 'GPT-4-8K', 'GPT-4-32K', 'GPT-3.5-4K', 'GPT-3.5-16K'.

    Returns:
        int: The number of tokens remaining.
    """
    token_limits = {
        'gpt-4': 8000,
        'gpt-4-32K': 32000,
        'gpt-3.5-turbo': 4000,
        'gpt-3.5-turbo-16k': 16000,
    }

    if model not in token_limits:
        raise ValueError("Invalid model. Choose from 'GPT-4-8K', 'GPT-4-32K', 'GPT-3.5-4K', 'GPT-3.5-16K'.")

    tokens_remaining = token_limits[model] - token_count

    return tokens_remaining

def calculate_price(token_count: int, model: str) -> float:
    """
    Calculate the price based on token count and model type.

    Args:
        token_count (int): The count of tokens.
        model (str): The type of model. Accepts 'GPT-4-8K', 'GPT-4-32K', 'GPT-3.5-4K', 'GPT-3.5-16K'.

    Returns:
        float: The total cost.
    """
    pricing = {
        'gpt-4': {'input_cost': 0.03, 'output_cost': 0.06},
        'GPT-4-32K': {'input_cost': 0.06, 'output_cost': 0.12},
        'gpt-3.5-turbo': {'input_cost': 0.0015, 'output_cost': 0.002},
        'gpt-3.5-turbo-16k': {'input_cost': 0.003, 'output_cost': 0.004},
    }

    if model not in pricing:
        raise ValueError("Invalid model. Choose from 'GPT-4-8K', 'GPT-4-32K', 'GPT-3.5-4K', 'GPT-3.5-16K'.")

    cost_per_1k_tokens = pricing[model]['input_cost'] + pricing[model]['output_cost']
    total_cost = (token_count / 1000) * cost_per_1k_tokens

    return total_cost

def save_file(question, answer, directory='log/'):
    now = datetime.now()
    dt_string = now.strftime("%d-%m-%Y_%H-%M-%S")
    shortened_question = question[:60]
    with open(directory + dt_string + '_' + shortened_question, 'w') as f:
        f.write("# Question:\n")
        f.write(question + '\n')
        f.write("# Answer:\n")
        f.write(answer)

def ask_question(question, model, prompt_background_question):
    if st.button("Ask"):
        if question:
            answer = send_message(prompt_background_question, model=model)
            st.write(answer)

            now = datetime.now()
            dt_string = now.strftime("%d-%m-%Y_%H-%M-%S")
            shortened_question = question[:60]
            with open('log/' + dt_string + '_' + shortened_question, 'w') as f:
                f.write("# Question:\n")
                f.write(question + '\n')
                f.write("# Answer:\n")
                f.write(answer)
        else:
            st.write("Please enter a question.")

if __name__ == "__main__":
    load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")
    create_directories()

    st.title('AI Application Template')
    model = st.radio("Select model", ('gpt-3.5-turbo', 'gpt-3.5-turbo-16k','gpt-4'))

    number_of_previous_conversations = st.slider("Select number of previous conversations to include", 0, 10, 5)

    # load base prompt
    with open("prompts/base_prompts", "r") as f:
        base_prompt = f.read()

    # display base_prompt if checkbox is checked
    if st.checkbox("Show base prompt"):
        st.write(base_prompt)

    dir_path = 'log/'
    list_of_files = os.listdir(dir_path)

    # # get the most recent file
    if list_of_files:
        latest_file = max(list_of_files, key=lambda x: os.path.getctime(os.path.join(dir_path, x)))

    # get recent files
    latest_files = sorted(list_of_files, key=lambda x: os.path.getctime(os.path.join(dir_path, x)), reverse=True)[:number_of_previous_conversations]

    # Show filenames for previous conversations
    if st.checkbox("Show filenames for previous conversations"):
        st.write(latest_files)

    previous_conversation = []

    for file in latest_files:
        # read the file
        with open('log/' + file, 'r') as f:
            # read the contents
            contents = f.read()
            # add the contents to the list
            previous_conversation.append(contents)

    # join the list into a string separated by newlines
    previous_conversation.reverse()
    previous_conversation_str = '\n'.join(previous_conversation)

    # display the last question and answer if checkbox is checked
    if st.checkbox("Show previous conversation"):
        st.write(previous_conversation_str)

    question = st.text_area("Question: ", value="", key="question")

    prompt_background_question = base_prompt + '\n' + previous_conversation_str + '\n' + "# Question or Statement:" + '\n' + question

    st.write("Number of tokens in message to send(does not include the current question): ", num_tokens_from_string(prompt_background_question, model=model))
    st.write("Tokens remaining: ", calculate_tokens_remaining(num_tokens_from_string(prompt_background_question, model=model), model=model))
    st.write("Cost to send message not including cost of the response: $", calculate_price(num_tokens_from_string(prompt_background_question, model=model), model=model))

    ask_question(question, model, prompt_background_question)