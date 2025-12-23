from transformers import pipeline

chat_pipeline = pipeline("text-generation", model="gpt2", device=-1)

def local_chat(user_text, emotion, face_detected, distance):
    if not user_text:
        return "woof woof"

    prompt = f"[emotion:{emotion}, face:{face_detected}, dist:{distance:.1f}] User:{user_text}\nRobot:"
    res = chat_pipeline(prompt, max_new_tokens=40, do_sample=True)
    return res[0]["generated_text"].split("Robot:")[-1][:100]