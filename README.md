# Python Password Manager 
## Kirabo Faith Kiggundu
## BSCS 2:2
## S24B23/083
Forked from [clxmente/Python-Password-Manager](https://github.com/clxmente/Python-Password-Manager)

## Project Description
This is a command-line password manager that uses AES(Advanced Encryption Standard) encryption to securely store 
passwords for different websites, protected by a master password.

---

## Changes Made

### 1. Logging

#### Problem Found in the Original Code
The original project had **zero logging**. This is a serious gap for a 
security application like a password manager because:
- There was no way to know if someone was repeatedly trying wrong master 
  passwords
- No record existed of when passwords were added, retrieved, or deleted
- If the program crashed, there was no log to help diagnose what went wrong
- Silent failures like corrupted files or OS errors left no trace behind

#### How I Fixed It
I added Python's built-in `logging` module to record important events to 
both the terminal and a log file called `app.log`.

Log levels used:
- `INFO` — successful actions e.g. login, password saved, password deleted
- `WARNING` — failed login attempts, empty inputs, invalid menu choices
- `ERROR` — corrupted files, OS errors, decryption failures

### 2. Exception Handling

#### Problems Found in the Original Code
- **No protection on file reads** — opening `masterpassword.json` and 
  `passwords.json` had no error handling. If either file was corrupted, 
  the program crashed with a raw Python traceback that exposed internal 
  file paths to the user.
- **`generate_password()` crashed on letters** — the original code called 
  `int(length)` directly without checking if the input was actually a 
  number. Typing `abc` instead of `8` can throw an unhandled `ValueError` and 
  crashes the entire program.
- **Silent failures on invalid menu choices** — typing `7` or `abc` at 
  the menu returned `None` silently. The user received no feedback and 
  nothing happened.
- **`split(':')` was unsafe** — retrieving a password split the result on 
  `:` using `split(':')[1]`. If a website name contained a colon, this 
  caused an `IndexError` crash.
- **Empty inputs accepted silently** — the original code looped 
  recursively on empty website and password inputs without telling the 
  user why nothing was happening.
- **No disk error protection** — all file write operations had no 
  `OSError` handling. A full disk or permission error would crash the 
  program with a system-level error message.

#### How I Fixed Each Problem
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
- **Empty inputs** — added explicit validation with clear user-facing 
  error messages instead of silent recursive loops

### 3. Input Validation

#### Problems Found in the Original Code
- Empty master password was accepted and compared against the stored hash, 
  always failing silently and re-prompting with no explanation
- Empty website names caused silent recursive loops with no user feedback
- Empty passwords were accepted and encrypted, storing a blank password
- Invalid Yes/No responses on confirmation prompts were silently ignored

#### How I Fixed Each Problem
- Empty master password is now rejected with a clear message
- Empty website name is now rejected with a clear message
- Empty password is now rejected with a clear message
- Invalid menu choices (e.g. `7`, `abc`) now show an error instead of 
  silently doing nothing
- Invalid Yes/No responses on confirmation prompts now show an error message

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
## AI-Generated Logging vs Human Reasoning

As part of improving this project, I compared AI suggestions with human 
reasoning when deciding what to log and how.

### What AI suggested
AI tends to log everything systematically for every function entry, every 
file operation, every exception. It focuses on coverage, making sure no 
event goes unrecorded. For example, AI suggested logging every single file 
read and write operation with detailed error messages including the exact 
OS error code.

### What a human developer would think
A human developer thinks about logging from a user and maintainer 
perspective. A human prioritises:
- Security events first — failed login attempts, deleted databases
- User actions that cannot be undone — password deletion, full data wipe
- Errors that are hard to reproduce — corrupted files, disk errors

A human would skip logging routine successful reads because they clutter 
the log file and make it harder to spot real problems.

### Key difference
AI prioritises **completeness** — log everything just in case. Humans 
prioritise **relevance** — log only what helps you diagnose a real problem 
quickly. The best approach, used in this project, combines both: AI helped 
identify all the places worth logging, while human judgment decided which 
level (`INFO`, `WARNING`, `ERROR`) was appropriate for each event and 
which routine operations did not need logging at all.
