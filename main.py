import openai
import json

# Load your OpenAI API key from an environment variable or secret management service
api_key = "your_openai_api_key"
openai.api_key = api_key

def generate_learning_content(user_interest, prompt):
    content = openai.Completion.create(
        engine="davinci-codex",
        prompt=f"Generate a lesson plan about {user_interest}. {prompt}",
        max_tokens=200,
        n=1,
        stop=None,
        temperature=0.7,
    )

    return content.choices[0].text.strip()

def main():
    user_interest = "Python programming"
    prompt = "Explain the basics and provide a simple exercise."

    generated_content = generate_learning_content(user_interest, prompt)
    print(generated_content)

if __name__ == "__main__":
    main()
