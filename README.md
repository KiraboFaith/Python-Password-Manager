# Python Password Manager — Improved Fork

Forked from [clxmente/Python-Password-Manager](https://github.com/clxmente/Python-Password-Manager)

A command-line password manager that uses AES encryption to securely store 
passwords for different websites, protected by a master password.

---

## Changes Made

This fork improves the original project by adding **logging**, 
**exception handling**, and **input validation** across three files.

### 1. Logging
Added Python's built-in `logging` module to record important events to 
both the terminal and a log file called `app.log`.

Log levels used:
- `INFO` — successful actions e.g. login, password saved, password deleted
- `WARNING` — failed login attempts, empty inputs, invalid menu choices
- `ERROR` — corrupted files, OS errors, decryption failures

### 2. Exception Handling
The original code had several places where unexpected input or file 
problems would crash the program with an unhelpful system error. The 
following were fixed:

- **Corrupted database files** — added `json.JSONDecodeError` handling 
  when reading `masterpassword.json` and `passwords.json`
- **Disk/permission errors** — added `OSError` handling around all file 
  read and write operations
- **Invalid password length input** — added `ValueError` handling in 
  `generate_password()` so typing letters instead of a number no longer 
  crashes the program
- **Corrupted hex data** — added `ValueError` handling in `decrypt_data()` 
  for corrupted stored passwords
- **Colon in website name** — fixed `split(':')` to `split(':', 1)` to 
  prevent `IndexError` when a website name contains a colon

### 3. Input Validation
- Empty master password is now rejected with a clear message
- Empty website name is now rejected with a clear message  
- Empty password is now rejected with a clear message
- Invalid menu choices (e.g. `7`, `abc`) now show an error instead of 
  silently doing nothing
- Invalid Y/N responses on confirmation prompts now show an error message

---

## Files Changed
- `main.py`
- `modules/encryption.py`
- `modules/menu.py`

---

## How to Run
```bash
# Install dependencies
pip install -r requirements.txt

# Run the program
python main.py
```

---

## Log File
All events are saved to `app.log` in the project root. Example:
```
2026-03-21 17:00:00 | INFO     | main:45 | Password Manager started.
2026-03-21 17:00:05 | WARNING  | main:38 | Failed login attempt — incorrect master password entered.
2026-03-21 17:00:10 | INFO     | main:32 | Master password accepted. User logged in successfully.
2026-03-21 17:00:20 | INFO     | encryption:47 | Password saved successfully for website: google.com
```
