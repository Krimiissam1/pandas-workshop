# Meeting Room Booking Quick Start

This guide walks you through running the meeting-room booking example from scratch on macOS, Linux, or Windows.

## 1. Install Python
Make sure Python 3.8, 3.9, 3.10, or 3.11 is installed. On Windows you can download it from [python.org](https://www.python.org/downloads/windows/), or install [Miniconda](https://docs.conda.io/en/latest/miniconda.html) to get both Python and `conda`.

## 2. Open a Terminal
* **Windows**: Use *Command Prompt*, *PowerShell*, or *Windows Terminal*. If you installed Miniconda/Anaconda, open the **Anaconda Prompt**.
* **macOS/Linux**: Use your default terminal app.

All remaining commands should be typed in the terminal window.

## 3. Clone the Project
```bash
$ git clone https://github.com/stefmolin/pandas-workshop.git
$ cd pandas-workshop
```

If you downloaded the ZIP instead of cloning, unzip it and `cd` into the unzipped folder before continuing.

## 4. Create & Activate a Virtual Environment (Recommended)
```bash
$ python -m venv .venv
# macOS/Linux
$ source .venv/bin/activate
# Windows (Command Prompt)
> .venv\Scripts\activate
```
Your prompt should now start with `(.venv)` (or `(pandas_workshop)` if using `conda`).

## 5. Install Dependencies
You can either use the `make` helper or run the equivalent `pip` command directly.

### Option A: With `make`
```bash
(.venv) $ make install
```

### Option B: Without `make`
```bash
(.venv) $ python -m pip install --upgrade pip
(.venv) $ python -m pip install -r requirements.txt
```

## 6. Run the Automated Tests (Optional but Recommended)
```bash
(.venv) $ make test          # or: python -m unittest discover -s tests -p "test*.py" -v
```

A successful run ends with `OK`.

## 7. Launch the Dashboard
```bash
(.venv) $ make dash          # or: python dash_app.py
```

The Dash development server will print an address such as `http://127.0.0.1:8050/`. Open that link in your browser to access the interface.

## 8. Stop the Dashboard
Press `Ctrl+C` in the terminal window running the server.

## 9. Deactivate the Virtual Environment (When Finished)
```bash
(.venv) $ deactivate
```

You can always re-activate the environment later and repeat steps 6–8.

---
Need help? Double-check each command for typos and ensure you are running them from the project directory (`pandas-workshop`).
