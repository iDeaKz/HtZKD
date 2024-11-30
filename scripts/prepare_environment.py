import os
import subprocess

def install_missing_dependencies():
    """
    Installs missing dependencies dynamically from requirements.txt.
    """
    print("Installing missing dependencies...")
    subprocess.run(["python", "-m", "pip", "install", "--upgrade", "pip"])
    subprocess.run(["pip", "install", "-r", "requirements.txt"])

def clean_temp_files():
    """
    Cleans up temporary files created during tests.
    """
    print("Cleaning up temporary files...")
    files_to_remove = ["test_patient_data.csv", "test_patient_data.xlsx", "test_patient_data.json"]
    for file in files_to_remove:
        file_path = f"app/data/{file}"
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Removed: {file_path}")

if __name__ == "__main__":
    install_missing_dependencies()
    clean_temp_files()
