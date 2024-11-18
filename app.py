import os
import getpass
from flask import Flask, render_template, request, jsonify, send_file
from ibm_watsonx_ai.foundation_models import Model
from io import BytesIO

app = Flask(__name__)

# --- IBM Watsonx Credentials (replace with your own) ---
def get_credentials():
    return {
        "url": "https://us-south.ml.cloud.ibm.com",
        "apikey": "RXVVFRLut0v9fMWKTbhyBWP23X4t_mxa4_D62bDL7_Zb"  # Replace with your actual API key
    }

model_id = "ibm/granite-13b-chat-v2"
parameters = {
    "decoding_method": "greedy",
    "max_new_tokens": 1500,
    "stop_sequences": ["\n\n"],
    "repetition_penalty": 1
}
project_id = "9266586e-7e62-4930-8201-81787ae9d328" # Replace with your project ID

model = Model(
    model_id=model_id,
    params=parameters,
    credentials=get_credentials(),
    project_id=project_id
)

@app.route("/", methods=["GET", "POST"])
def index():
    answer = None
    if request.method == "POST":
        article = request.form["article"]
        question_type = request.form["question_type"]
        num_questions = int(request.form.get("num_questions", 5))

        try:
            few_shot_prompts = f"""
### Example 1: {question_type}
Article:
###
Farmers are among the most vulnerable to climate change, yet they also hold the potential to be some of its greatest problem-solvers.
###

Question Paper:
###
1. What are the dual roles of farmers in the context of climate change?
   A. Victims only
   B. Problem-solvers only
   C. Both vulnerable and potential problem-solvers
   D. None of the above
   Answer: C
###
"""

            full_prompt = f"""{few_shot_prompts}

You are a helpful AI assistant who can write question papers for examinations. Write {num_questions} {question_type} questions and their answer scripts in markdown format, based on the provided article. If the article does not contain sufficient information to answer a question, indicate "I don't know" as the answer.

Article: 
###
{article}
###

Generate the question paper below:
"""

            generated_response = model.generate_text(prompt=full_prompt, guardrails=True)
            answer = generated_response.strip()

            if "I don't know" in answer or not answer:
                return jsonify({"error": "Could not generate questions. Check article content."})

        except Exception as e:
            return jsonify({"error": f"An error occurred: {str(e)}"})

    return render_template("index.html", answer=answer)

@app.route("/download", methods=["POST"])
def download_questions():
    institute = request.form.get("institute")
    exam_type = request.form.get("exam_type")
    date = request.form.get("date")
    duration = request.form.get("duration")
    questions = request.form.get("questions")
    include_answers = request.form.get("include_answers")

    if not all([institute, exam_type, date, duration, questions]):
        return jsonify({"error": "Missing form data."})

    if include_answers == "yes":
        content = f"Institute: {institute}\nExam Type: {exam_type}\nDate: {date}\nDuration: {duration}\n\n{questions}"
    else:
        content = f"Institute: {institute}\nExam Type: {exam_type}\nDate: {date}\nDuration: {duration}\n\n"
        for line in questions.splitlines():
            if not line.startswith("Answer:"):
                content += line + "\n"

    mem = BytesIO()
    mem.write(content.encode('utf-8'))
    mem.seek(0)

    return send_file(
        mem,
        mimetype="text/plain",
        as_attachment=True,
        download_name="questions.txt"
    )

if __name__ == "__main__":
    app.run(debug=True)
