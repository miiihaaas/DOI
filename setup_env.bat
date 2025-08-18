@echo off
echo Creating Python virtual environment...
python -m venv venvDOI

echo Activating virtual environment...
call venvDOI\Scripts\activate.bat

echo Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

echo Virtual environment setup complete!
echo To activate: venvDOI\Scripts\activate.bat
echo To deactivate: deactivate