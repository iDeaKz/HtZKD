import subprocess
import re

def install_dependency(dependency, requirements_fixed):
    try:
        # Attempt to install the dependency
        print(f"Trying to install: {dependency}")
        subprocess.run(["pip", "install", dependency], check=True)
        requirements_fixed.append(dependency)  # Save successful installs
    except subprocess.CalledProcessError as e:
        print(f"Failed to install: {dependency}. Error: {e}")
        handle_dependency_error(dependency, requirements_fixed)

def handle_dependency_error(dependency, requirements_fixed):
    name, version = None, None
    # Extract name and version
    match = re.match(r"([a-zA-Z0-9\-_.]+)(==|>=|<=|>|<)?([0-9.]+)?", dependency)
    if match:
        name, operator, version = match.groups()
        print(f"Checking for alternatives for: {name}")
    else:
        print(f"Could not parse dependency: {dependency}. Skipping.")
        return
    
    # Get available versions
    result = subprocess.run(["pip", "index", "versions", name], capture_output=True, text=True)
    if result.returncode == 0:
        print(result.stdout)
        # Display options for the user
        print(f"Available versions for {name}:")
        available_versions = re.findall(r"Available versions: (.+)", result.stdout)
        if available_versions:
            print(", ".join(available_versions))
        else:
            print("No versions found.")
    else:
        print(f"Failed to retrieve versions for {name}. Skipping.")
        return

    # Ask user for input
    new_version = input(f"Enter a valid version for {name} (or skip by pressing Enter): ").strip()
    if new_version:
        fixed_dependency = f"{name}=={new_version}"
        install_dependency(fixed_dependency, requirements_fixed)
    else:
        print(f"Skipping: {name}")

def main():
    input_file = "requirements.txt"
    output_file = "requirements_fixed.txt"
    
    requirements_fixed = []
    
    with open(input_file, "r") as file:
        dependencies = file.readlines()
    
    for dependency in dependencies:
        dependency = dependency.strip()
        if dependency:
            install_dependency(dependency, requirements_fixed)
    
    # Save fixed requirements
    with open(output_file, "w") as file:
        file.write("\n".join(requirements_fixed))
    
    print(f"Updated requirements saved to {output_file}.")

if __name__ == "__main__":
    main()
