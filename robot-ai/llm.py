from transformers import pipeline

chat_pipeline = pipeline("text-generation", model="gpt2", device=-1)

def local_chat(user_text, emotion, face_detected, distance):
    if not user_text:
        return "woof woof"

    prompt = (
        f"[context: emotion={emotion}, face_detected={face_detected}, distance={distance:.1f}m]\n"
        f"User: {user_text}\n"
        "Robot: (responds in a friendly and natural tone)"
    )
    res = chat_pipeline(prompt, max_new_tokens=40, do_sample=True)
    return res[0]["generated_text"].split("Robot:")[-1][:100]