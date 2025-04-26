import os
from dotenv import load_dotenv

# Lädt die Umgebungsvariablen aus der .env-Datei
load_dotenv()

def main():
    secret_key = os.getenv("SECRET_KEY", "default_key")
    print(f"Your secret key is: {secret_key}")

if __name__ == "__main__":
    main()
