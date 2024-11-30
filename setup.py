from setuptools import setup, find_packages

# Read the README file for the long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="HtZkaediHealingSolution",
    version="0.1.0",
    author="zkaedi",
    author_email="your.email@example.com",
    description="Interactive dashboard for monitoring patient healing processes.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/HtZkaediHealingSolution",
    packages=find_packages(),
    include_package_data=True,  # Includes files from MANIFEST.in
    install_requires=[
        "dash==2.9.3"
        "dash-bootstrap-components==1.3.1"
        "flask>=2.3.2"
        "flask-sqlalchemy>=3.0.0"
        "pandas==1.5.3"
        "numpy==1.24.3"
        "plotly==5.15.0"
        "requests==2.31.0"
        "setuptools>=65.5.0"
        "SQLAlchemy==1.4.47"
        "psycopg2-binary==2.9.6"
        "alembic==1.11.1"
        "flask-login>=0.6.3"
        "werkzeug>=2.3.6"
        "bcrypt==4.0.1"
        "python-dotenv==1.0.0"
        "pytest>=7.4.0"
        "pytest-cov==4.0.0"
        "coverage==7.3.1"
        "celery==5.3.1"
        "redis==4.5.5"
        "bleak>=0.22.0"
        "psutil>=5.9.0"
        "openpyxl>=3.1.2"

        

    ],
    extras_require={
        "dev": [
            "flake8",
            "black",
            "isort",
            "mypy",
            "pre-commit",
            "pytest",
            "pytest-cov",
            "coverage"
        ],
        "docs": [
            "sphinx",
            "sphinx_rtd_theme"
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",  # Update if different
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)
