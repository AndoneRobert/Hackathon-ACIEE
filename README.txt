PROJECT SETUP INSTRUCTIONS
==========================

This project relies on specific Python libraries. To run the code, you must
install these dependencies using the "requirements.txt" file.

Follow these steps to set up your environment:

1. PREREQUISITES
   Ensure you have Python 3 installed on your system.
   Check by running: python3 --version

2. CREATE A VIRTUAL ENVIRONMENT
   It is recommended to use a virtual environment to avoid conflicts.
   Run the following command in the project root folder:
   
   python3 -m venv .venv

3. ACTIVATE THE VIRTUAL ENVIRONMENT
   
   - On Linux / MacOS:
     source .venv/bin/activate

   - On Windows (Command Prompt):
     .venv\Scripts\activate.bat

   - On Windows (PowerShell):
     .venv\Scripts\Activate.ps1

4. INSTALL DEPENDENCIES
   Once the environment is active (you should see (.venv) in your terminal),
   install the required libraries:

   pip install -r requirements.txt

5. RUN THE PROJECT
   You are now ready to run the Python scripts.