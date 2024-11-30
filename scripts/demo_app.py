# scripts/demo_app.py

import time
import random
from app.utils.metrics import record_request_metrics, start_metrics_server

def process_request():
    """
    Simulates processing a request.
    """
    process_time = random.uniform(0.1, 2.0)  # Random processing time between 0.1 and 2 seconds
    time.sleep(process_time)
    return process_time

def main():
    """
    Main function to simulate a running application with Prometheus metrics.
    """
    # Start metrics server
    start_metrics_server(port=8001)
    
    print("Simulating requests. Press Ctrl+C to stop.")
    while True:
        try:
            process_time = process_request()
            record_request_metrics(process_time)
        except KeyboardInterrupt:
            print("Shutting down...")
            break

if __name__ == "__main__":
    main()
