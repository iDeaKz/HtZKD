import subprocess

def run_tests():
    """
    Runs tests with detailed logs and coverage reports.
    """
    print("Running tests with pytest...")
    result = subprocess.run([
        "pytest", 
        "--cov=app", 
        "--cov-report=xml", 
        "--maxfail=5", 
        "--dist=loadscope", 
        "-n", "auto", 
        "-v", 
        "--log-cli-level=DEBUG"
    ])
    if result.returncode == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed. Check the logs for details.")
        exit(1)

if __name__ == "__main__":
    run_tests()
