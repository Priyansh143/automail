import yaml
import subprocess
import json

#  1. Load Profile 
def load_profile(path="config/profile.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)

#  2. Load Local Ollama Model 
def load_model_ollama(model_name="gemma3:4b"):
    result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
    if model_name.split(":")[0] not in result.stdout:
        raise Exception(f"Model {model_name} not found. Run `ollama pull {model_name}` first.")
    print(f"✅ Using local Ollama model: {model_name}")
    return model_name

#  3. Generate Email Reply with Ollama
def generate_reply(email_body: str, sender: str, profile: dict, model_name="gemma3:4b") -> str:
    prompt = (
        f"You are {profile['name']}, a {profile['role']}. You have skills {profile['skills']}. "
        f"Write a concise and {profile.get('preferred_tone', 'professional')} reply to the email below:\n\n"
        f"From: {sender}\n"
        f"Message: {email_body}\n\n"
        "Reply:\n"
    )

    response = subprocess.run(
    ["ollama", "run", model_name],
    input=prompt,
    text=True,
    capture_output=True,
    encoding="utf-8",   
    errors="ignore"     
    )

    if response.returncode != 0:
        raise RuntimeError(f"❌ Ollama Error:\n{response.stderr}")

    return response.stdout.strip()

# # ✅ 4. Standalone Test
# if __name__ == "__main__":
#     profile = load_profile()
#     model_name = load_model_ollama()

#     sample_email = (
#         "Hi Neo, we’d love to schedule a quick call to discuss the role at TechNova. "
#         "Are you available this week?"
#     )
#     sender = "Alex from TechNova"

#     reply = generate_reply(sample_email, sender, profile, model_name)
#     print("\n📧 Auto-Reply:\n", reply)
