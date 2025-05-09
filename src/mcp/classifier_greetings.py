class GreetingClassifier:
    def __init__(self, query_generator):
        self.query_generator = query_generator

    def classify(self, user_input):
        prompt = f"""
Determine if this input is a greeting or a question:
"{user_input}"
Respond with GREETING or QUESTION only.
"""

        response = self.query_generator.client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a user input classifier."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=10,
            temperature=0.0,
            top_p=1.0
        )

        classification = response.choices[0].message.content.strip().upper()

        if classification == "GREETING":
            return "N/A", {"message": "Hello! How can I assist you today?"}
        elif classification == "QUESTION":
            # ...proceed with normal question handling...
            pass
        else:
            return "N/A", {"message": "Sorry, I couldn't classify your input. Please try again."}