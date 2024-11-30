#!/bin/bash

# Check Chrome version
echo "Checking Chrome version..."
google-chrome --version || echo "Google Chrome is not installed."

# Check ChromeDriver version
echo "Checking ChromeDriver version..."
chromedriver --version || echo "ChromeDriver is not installed."

# Add ChromeDriver to PATH if necessary
export PATH=$PATH:/usr/local/bin/chromedriver
echo "ChromeDriver path set to $PATH."
