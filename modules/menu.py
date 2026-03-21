import sys
import getpass
import logging
import pyperclip

from termcolor import colored
from halo import Halo

from modules.encryption import DataManip
from modules.exceptions import *

logger = logging.getLogger(__name__)

class Manager:
    def __init__(self, obj: DataManip, filename: str, master_file: str, master_pass: str):
        self.obj_ = obj
        self.filename_ = filename
        self.master_file_ = master_file
        self.master_pass_ = master_pass

    def begin(self):
        try:
            choice = self.menu_prompt()
        except UserExits:
            raise UserExits

        if choice == '4':
            raise UserExits

        if choice == '1':
            try:
                self.update_db()
                return self.begin()
            except UserExits:
                raise UserExits

        elif choice == '2':
            try:
                result = self.load_password()
                # FIX: use split(':', 1) to handle website names that contain colons
                parts = result.split(':', 1)
                if len(parts) != 2:
                    logger.error("Unexpected format when loading password — could not split result.")
                    print(colored("Error: Could not read password data correctly.", "red"))
                    return self.begin()
                website = parts[0]
                password = parts[1]
                logger.info("Password retrieved for website: %s", website)
                print(colored(f"Password for {website}: {password}", "yellow"))

                copy_to_clipboard = input("Copy password to clipboard? (Y/N): ").strip()
                if copy_to_clipboard.lower() == "exit":
                    raise UserExits
                elif copy_to_clipboard.lower() == 'y':
                    try:
                        pyperclip.copy(password)
                        print(colored(f"{self.obj_.checkmark_} Password copied to clipboard", "green"))
                    except pyperclip.PyperclipException:
                        print(colored(f"{self.obj_.x_mark_} If you see this on Linux use `sudo apt-get install xsel` for copying to work. {self.obj_.x_mark_}", "red"))
                else:
                    pass
                return self.begin()
            except UserExits:
                raise UserExits
            except PasswordFileDoesNotExist:
                print(colored(f"{self.obj_.x_mark_} DB not found. Try adding a password {self.obj_.x_mark_}", "red"))
                return self.begin()

        elif choice == '3':
            try:
                return self.delete_password()
            except UserExits:
                raise UserExits

        elif choice == '5':
            try:
                self.delete_db(self.master_pass_)
            except MasterPasswordIncorrect:
                print(colored(f"{self.obj_.x_mark_} Master password is incorrect {self.obj_.x_mark_}", "red"))
                return self.delete_db(self.master_pass_)
            except UserExits:
                raise UserExits

        elif choice == '6':
            try:
                self.delete_all_data(self.master_pass_)
            except MasterPasswordIncorrect:
                print(colored(f"{self.obj_.x_mark_} Master password is incorrect {self.obj_.x_mark_}", "red"))
                return self.delete_all_data(self.master_pass_)
            except UserExits:
                raise UserExits

        else:
            # FIX: invalid menu choices now warn the user instead of silently doing nothing
            logger.warning("Invalid menu choice entered: '%s'", choice)
            print(colored(f"{self.obj_.x_mark_} Invalid choice '{choice}'. Please enter a number between 1 and 6. {self.obj_.x_mark_}", "red"))
            return self.begin()

    def menu_prompt(self):
        """Asks user for a choice from Menu"""
        print(colored("\n\t*Enter 'exit' at any point to exit.*\n", "magenta"))
        print(colored("1) Add/Update a password", "blue"))
        print(colored("2) Look up a stored password", "blue"))
        print(colored("3) Delete a password", "blue"))
        print(colored("4) Exit program", "blue"))
        print(colored("5) Erase all passwords", "red"))
        print(colored("6) Delete all data including Master Password", "red"))

        choice = input("Enter a choice: ")

        if choice == "":
            return self.menu_prompt()
        elif choice.strip() == "exit":
            raise UserExits
        else:
            return choice.strip()

    def __return_generated_password(self, website):
        """Returns a generated password"""
        try:
            generated_pass = self.obj_.generate_password()
            print(colored(generated_pass, "yellow"))

            loop = input("Generate a new password? (Y/N): ")
            if loop.lower().strip() == "exit":
                raise UserExits
            elif (loop.lower().strip() == 'y') or (loop.strip() == ""):
                return self.__return_generated_password(website)
            elif loop.lower().strip() == 'n':
                return generated_pass
        except (PasswordNotLongEnough, EmptyField):
            print(colored("Password length invalid. Must be a number and at least 8 characters.", "red"))
            return self.__return_generated_password(website)
        except UserExits:
            print(colored("Exiting...", "red"))
            sys.exit()

    def update_db(self):
        """Add or update a password in the DB"""
        try:
            self.list_passwords()
        except PasswordFileIsEmpty:
            pass
        except PasswordFileDoesNotExist:
            print(colored("--There are no passwords stored.--", "yellow"))

        website = input("Enter the website for which you want to store a password (ex. google.com): ")
        if website.strip() == "":
            # FIX: inform user instead of silently looping
            print(colored("Website name cannot be empty. Please try again.", "red"))
            return self.update_db()
        elif website.lower().strip() == "exit":
            raise UserExits
        else:
            gen_question = input("Do you want to generate a password for {} ? (Y/N): ".format(website))
            if gen_question.strip() == "":
                print(colored("Please enter Y or N.", "red"))
                return self.update_db()
            elif gen_question.lower().strip() == "exit":
                raise UserExits
            elif gen_question.lower().strip() == 'n':
                password = input("Enter a password for {}: ".format(website))
                if password.strip() == "":
                    # FIX: catch empty password input
                    logger.warning("User attempted to save an empty password for: %s", website)
                    print(colored("Password cannot be empty. Please try again.", "red"))
                    return self.update_db()
                elif password.lower().strip() == "exit":
                    raise UserExits
                else:
                    self.obj_.encrypt_data(self.filename_, password, self.master_pass_, website)
            elif gen_question.lower().strip() == 'y':
                password = self.__return_generated_password(website)
                self.obj_.encrypt_data("db/passwords.json", password, self.master_pass_, website)
            else:
                # FIX: handle invalid Y/N response on generate question
                print(colored("Please enter Y or N.", "red"))
                return self.update_db()

    def load_password(self):
        """Loads and decrypts a password for a given website"""
        try:
            self.list_passwords()
        except PasswordFileIsEmpty:
            return self.begin()

        website = input("Enter website for the password you want to retrieve: ")

        if website.lower().strip() == "exit":
            raise UserExits
        elif website.strip() == "":
            print(colored("Website name cannot be empty. Please try again.", "red"))
            return self.load_password()
        else:
            try:
                plaintext = self.obj_.decrypt_data(self.master_pass_, website, self.filename_)
            except PasswordNotFound:
                logger.warning("Password lookup failed — no entry found for: %s", website)
                print(colored(f"{self.obj_.x_mark_} Password for {website} not found {self.obj_.x_mark_}", "red"))
                return self.load_password()
            except PasswordFileDoesNotExist:
                print(colored(f"{self.obj_.x_mark_} DB not found. Try adding a password {self.obj_.x_mark_}", "red"))
                return self.begin()

            final_str = f"{website}:{plaintext}"
            return final_str

    def delete_db(self, stored_master):
        """Menu Prompt to Delete DB/Passwords"""
        confirmation = input("Are you sure you want to delete the password file? (Y/N): ")
        if confirmation.lower().strip() == 'y':
            entered_master = getpass.getpass("Enter your master password to delete all stored passwords: ")
            if entered_master.lower().strip() == "exit":
                raise UserExits
            else:
                try:
                    self.obj_.delete_db(self.filename_, stored_master, entered_master)
                    print(colored(f"{self.obj_.checkmark_} Password Data Deleted successfully. {self.obj_.checkmark_}", "green"))
                    return self.begin()
                except MasterPasswordIncorrect:
                    raise MasterPasswordIncorrect
                except PasswordFileDoesNotExist:
                    print(colored(f"{self.obj_.x_mark_} DB not found. Try adding a password {self.obj_.x_mark_}", "red"))
                    return self.begin()
        elif confirmation.lower().strip() == 'n':
            logger.info("User cancelled password database deletion.")
            print(colored("Cancelling...", "red"))
            return self.begin()
        elif confirmation.lower().strip() == "exit":
            raise UserExits
        elif confirmation.strip() == "":
            return self.delete_db(stored_master)
        else:
            # FIX: handle invalid Y/N input on deletion confirmation
            print(colored("Please enter Y or N.", "red"))
            return self.delete_db(stored_master)

    def list_passwords(self):
        """Lists all websites stored in DB"""
        print(colored("Current Passwords Stored:", "yellow"))
        spinner = Halo(text=colored("Loading Passwords", "yellow"), color="yellow", spinner=self.obj_.dots_)

        try:
            lst_of_passwords = self.obj_.list_passwords(self.filename_)
            spinner.stop()
            print(colored(lst_of_passwords, "yellow"))
        except PasswordFileIsEmpty:
            lst_of_passwords = "--There are no passwords stored.--"
            spinner.stop()
            print(colored(lst_of_passwords, "yellow"))
            raise PasswordFileIsEmpty
        except PasswordFileDoesNotExist:
            raise PasswordFileDoesNotExist

    def delete_password(self):
        """Deletes a single password from DB"""
        try:
            self.list_passwords()
        except PasswordFileIsEmpty:
            return self.begin()

        website = input("What website do you want to delete? (ex. google.com): ").strip()

        if website == "exit":
            raise UserExits
        elif website == "":
            print(colored("Website name cannot be empty. Please try again.", "red"))
            return self.delete_password()
        else:
            try:
                self.obj_.delete_password(self.filename_, website)
                logger.info("Password deleted for website: %s", website)
                print(colored(f"{self.obj_.checkmark_} Data for {website} deleted successfully.", "green"))
                return self.begin()
            except PasswordNotFound:
                logger.warning("Delete failed — no entry found for: %s", website)
                print(colored(f"{self.obj_.x_mark_} {website} not in DB {self.obj_.x_mark_}", "red"))
                return self.delete_password()
            except PasswordFileDoesNotExist:
                print(colored(f"{self.obj_.x_mark_} DB not found. Try adding a password {self.obj_.x_mark_}", "red"))
                return self.begin()

    def delete_all_data(self, stored_master):
        """Deletes ALL data including master password and passwords stored."""
        confirmation = input("Are you sure you want to delete all data? (Y/N): ")
        if confirmation.lower().strip() == 'y':
            entered_master = getpass.getpass("Enter your master password to delete all stored passwords: ")
            if entered_master.lower().strip() == "exit":
                raise UserExits
            else:
                try:
                    self.obj_.delete_all_data(self.filename_, self.master_file_, stored_master, entered_master)
                    print(colored(f"{self.obj_.checkmark_} All Data Deleted successfully. {self.obj_.checkmark_}", "green"))
                    sys.exit()
                except MasterPasswordIncorrect:
                    raise MasterPasswordIncorrect
        elif confirmation.lower().strip() == 'n':
            logger.info("User cancelled full data deletion.")
            print(colored("Cancelling...", "red"))
            return self.begin()
        elif confirmation.lower().strip() == "exit":
            raise UserExits
        elif confirmation.strip() == "":
            return self.delete_all_data(stored_master)
        else:
            # FIX: handle invalid Y/N input on full deletion confirmation
            print(colored("Please enter Y or N.", "red"))
            return self.delete_all_data(stored_master)
