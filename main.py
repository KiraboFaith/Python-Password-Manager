import os
import json
import sys
import getpass
import logging

from hashlib import sha256
from termcolor import colored
from halo import Halo

from modules.encryption import DataManip
from modules.exceptions import UserExits, PasswordFileDoesNotExist
from modules.menu import Manager

# ── Logging Setup ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(module)s:%(lineno)d | %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
# ──────────────────────────────────────────────────────────────

def exit_program():
    logger.info("User exited the program.")
    print(colored("Exiting...", "red"))
    sys.exit()

def start(obj: DataManip):
    if os.path.isfile("db/masterpassword.json"):

        # FIX: catch corrupted or invalid JSON in the master password file
        try:
            with open("db/masterpassword.json", 'r') as jsondata:
                jfile = json.load(jsondata)
        except json.JSONDecodeError:
            logger.error("Master password file is corrupted and could not be read.")
            print(colored("Error: Master password file is corrupted. Please delete db/masterpassword.json and restart.", "red"))
            sys.exit(1)
        except OSError as e:
            logger.error("Could not open master password file: %s", e)
            print(colored("Error: Could not open master password file.", "red"))
            sys.exit(1)

        stored_master_pass = jfile["Master"]

        # FIX: validate that master password input is not empty
        master_password = getpass.getpass("Enter Your Master Password: ")
        if master_password.strip() == "":
            logger.warning("Empty master password entered.")
            print(colored("Master password cannot be empty. Please try again.", "red"))
            return start(obj)

        spinner = Halo(text=colored("Unlocking", "green"), color="green", spinner=obj.dots_)

        if sha256(master_password.encode("utf-8")).hexdigest() == stored_master_pass:
            logger.info("Master password accepted. User logged in successfully.")
            print(colored(f"{obj.checkmark_} Thank you! Choose an option below:", "green"))
            menu = Manager(obj, "db/passwords.json", "db/masterpassword.json", master_password)

            try:
                menu.begin()
            except UserExits:
                exit_program()
            except PasswordFileDoesNotExist:
                logger.error("Password database file not found after login.")
                print(colored(f"{obj.x_mark_} DB not found. Try adding a password {obj.x_mark_}", "red"))
        else:
            logger.warning("Failed login attempt — incorrect master password entered.")
            print(colored(f"{obj.x_mark_} Master password is incorrect {obj.x_mark_}", "red"))
            return start(obj)

    else:
        # First time running: create master password
        try:
            os.mkdir("db/")
        except FileExistsError:
            pass
        except OSError as e:
            logger.error("Could not create database directory: %s", e)
            print(colored("Error: Could not create database directory.", "red"))
            sys.exit(1)

        print(colored("To start, we'll have you create a master password. Be careful not to lose it as it is unrecoverable.", "green"))
        master_password = getpass.getpass("Create a master password for the program: ")

        # FIX: validate master password is not empty on creation
        if master_password.strip() == "":
            logger.warning("Empty master password entered during setup.")
            print(colored("Master password cannot be empty. Please try again.", "red"))
            return start(obj)

        second_input = getpass.getpass("Verify your master password: ")

        if master_password == second_input:
            spinner = Halo(text=colored("initializing base...", "green"), color="green", spinner=obj.dots_)
            hash_master = sha256(master_password.encode("utf-8")).hexdigest()
            jfile = {"Master": {}}
            jfile["Master"] = hash_master

            # FIX: catch file write errors during master password creation
            try:
                with open("db/masterpassword.json", 'w') as jsondata:
                    json.dump(jfile, jsondata, sort_keys=True, indent=4)
            except OSError as e:
                logger.error("Failed to save master password file: %s", e)
                print(colored("Error: Could not save master password. Check disk space and permissions.", "red"))
                sys.exit(1)

            spinner.stop()
            logger.info("Master password created successfully. Database initialized.")
            print(colored(f"{obj.checkmark_} Thank you! Restart the program and enter your master password to begin.", "green"))
        else:
            logger.warning("Master password creation failed — passwords did not match.")
            print(colored(f"{obj.x_mark_} Passwords do not match. Please try again {obj.x_mark_}", "red"))
            return start(obj)

if __name__ == "__main__":
    logger.info("Password Manager started.")
    obj = DataManip()
    start(obj)
