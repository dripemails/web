import openai
import config

api_key =config.api_key

openai.api_key = api_key

def generate_email(subject, recipient, tone="professional", length="medium"):
    prompt = f"Write a {tone} email to {recipient} about '{subject}'. The email should be {length} in length."

    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=250,
        n=1,
        stop=None,
        temperature=0.7,
    )

    email_content = response.choices[0].text.strip()
    return email_content