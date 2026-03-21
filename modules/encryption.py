import json
import string
import os
import random
import logging

from Crypto.Cipher import AES
from halo import Halo
from termcolor import colored

from modules.exceptions import *

logger = logging.getLogger(__name__)

class DataManip:
    def __init__(self):
        self.dots_ = {"interval": 80, "frames": ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]}
        self.checkmark_ = "\u2713"
        self.x_mark_ = "\u2717"
        self.specialChar_ = "!@#$%^&*()-_"

    def __save_password(self, filename, data, nonce, website):
        """Saves encrypted password to DB"""
        spinner = Halo(text=colored("Saving", "green"), spinner=self.dots_, color="green")
        spinner.start()

        try:
            if os.path.isfile(filename):
                try:
                    with open(filename, 'r') as jsondata:
                        jfile = json.load(jsondata)
                    jfile[website]["nonce"] = nonce
                    jfile[website]["password"] = data
                except KeyError:
                    with open(filename, 'r') as jsondata:
                        jfile = json.load(jsondata)
                    jfile[website] = {}
                    jfile[website]["nonce"] = nonce
                    jfile[website]["password"] = data
                except json.JSONDecodeError:
                    # FIX: handle corrupted password database file
                    logger.error("Password database file is corrupted and could not be read.")
                    spinner.stop()
                    print(colored("Error: Password database is corrupted.", "red"))
                    return
                with open(filename, 'w') as jsondata:
                    json.dump(jfile, jsondata, sort_keys=True, indent=4)
            else:
                jfile = {website: {}}
                jfile[website]["nonce"] = nonce
                jfile[website]["password"] = data
                with open(filename, 'w') as jsondata:
                    json.dump(jfile, jsondata, sort_keys=True, indent=4)
        except OSError as e:
            # FIX: catch disk/permission errors when saving
            logger.error("Failed to save password for %s due to OS error: %s", website, e)
            spinner.stop()
            print(colored("Error: Could not save password. Check disk space and permissions.", "red"))
            return

        spinner.stop()
        logger.info("Password saved successfully for website: %s", website)
        print(colored(f"{self.checkmark_} Saved successfully. Thank you!", "green"))

    def encrypt_data(self, filename, data, master_pass, website):
        """Encrypt and save the data to a file using master password as the key"""
        concatenated_master = master_pass + "================"
        key = concatenated_master[:16].encode("utf-8")
        cipher = AES.new(key, AES.MODE_EAX)
        nonce = cipher.nonce.hex()
        data_to_encrypt = data.encode("utf-8")
        encrypted_data = cipher.encrypt(data_to_encrypt).hex()
        self.__save_password(filename, encrypted_data, nonce, website)

    def decrypt_data(self, master_pass, website, filename):
        """Return a decrypted password as a string."""
        if os.path.isfile(filename):
            try:
                with open(filename, 'r') as jdata:
                    jfile = json.load(jdata)
                nonce = bytes.fromhex(jfile[website]["nonce"])
                password = bytes.fromhex(jfile[website]["password"])
            except KeyError:
                raise PasswordNotFound
            except json.JSONDecodeError:
                # FIX: handle corrupted database during decryption
                logger.error("Password database is corrupted — could not read during decryption.")
                raise PasswordFileDoesNotExist
            except ValueError as e:
                # FIX: handle corrupted hex data stored in the database
                logger.error("Corrupted password data for website '%s': %s", website, e)
                raise PasswordNotFound
            except OSError as e:
                logger.error("Could not read password file: %s", e)
                raise PasswordFileDoesNotExist
        else:
            raise PasswordFileDoesNotExist

        formatted_master_pass = master_pass + "================"
        master_pass_encoded = formatted_master_pass[:16].encode("utf-8")
        cipher = AES.new(master_pass_encoded, AES.MODE_EAX, nonce=nonce)
        plaintext_password = cipher.decrypt(password).decode("utf-8")
        return plaintext_password

    def generate_password(self):
        """Generates a complex password"""
        password = []
        length = input("Enter Length for Password (At least 8): ")

        if length.lower().strip() == "exit":
            raise UserExits
        elif length.strip() == "":
            raise EmptyField

        # FIX: catch non-numeric input instead of crashing with ValueError
        try:
            length_int = int(length)
        except ValueError:
            logger.warning("Invalid password length entered — not a number: '%s'", length)
            print(colored("Please enter a valid number for the password length.", "red"))
            return self.generate_password()

        if length_int < 8:
            raise PasswordNotLongEnough
        else:
            spinner = Halo(text=colored("Generating Password", "green"), spinner=self.dots_, color="green")
            spinner.start()
            for i in range(0, length_int):
                password.append(random.choice(random.choice([
                    string.ascii_lowercase,
                    string.ascii_uppercase,
                    string.digits,
                    self.specialChar_
                ])))
            finalPass = "".join(password)
            spinner.stop()
            return finalPass

    def list_passwords(self, filename):
        """Loads a list of websites in DB"""
        if os.path.isfile(filename):
            # FIX: catch corrupted database when listing passwords
            try:
                with open(filename, 'r') as jsondata:
                    pass_list = json.load(jsondata)
            except json.JSONDecodeError:
                logger.error("Password database is corrupted — could not list passwords.")
                raise PasswordFileDoesNotExist
            except OSError as e:
                logger.error("Could not read password file: %s", e)
                raise PasswordFileDoesNotExist

            passwords_lst = ""
            for i in pass_list:
                passwords_lst += "--{}\n".format(i)
            if passwords_lst == "":
                raise PasswordFileIsEmpty
            else:
                return passwords_lst
        else:
            raise PasswordFileDoesNotExist

    def delete_db(self, filename, stored_master, entered_master):
        """Delete DB/Password file & contents"""
        if os.path.isfile(filename):
            if stored_master == entered_master:
                spinner = Halo(text=colored("Deleting all password data...", "red"), spinner=self.dots_, color="red")
                # FIX: catch OS errors when deleting the database
                try:
                    jfile = {}
                    with open(filename, 'w') as jdata:
                        json.dump(jfile, jdata)
                    os.remove(filename)
                except OSError as e:
                    logger.error("Failed to delete password database: %s", e)
                    spinner.stop()
                    print(colored("Error: Could not delete password database.", "red"))
                    return
                spinner.stop()
                logger.warning("Password database deleted by user.")
            else:
                raise MasterPasswordIncorrect
        else:
            raise PasswordFileDoesNotExist

    def delete_password(self, filename, website):
        """Deletes a single password from DB"""
        if os.path.isfile(filename):
            # FIX: catch corrupted database during single password deletion
            try:
                with open(filename, 'r') as jdata:
                    jfile = json.load(jdata)
            except json.JSONDecodeError:
                logger.error("Password database is corrupted — could not delete password for %s.", website)
                raise PasswordFileDoesNotExist
            except OSError as e:
                logger.error("Could not read password file for deletion: %s", e)
                raise PasswordFileDoesNotExist

            try:
                jfile.pop(website)
                with open("db/passwords.json", 'w') as jdata:
                    json.dump(jfile, jdata, sort_keys=True, indent=4)
                logger.info("Password deleted for website: %s", website)
            except KeyError:
                raise PasswordNotFound
            except OSError as e:
                logger.error("Failed to write updated password file after deletion: %s", e)
                print(colored("Error: Could not save changes after deletion.", "red"))
        else:
            raise PasswordFileDoesNotExist

    def delete_all_data(self, filename, master_file, stored_master, entered_master):
        """Deletes ALL data including master password and passwords stored"""
        if os.path.isfile(master_file) and os.path.isfile(filename):
            if stored_master == entered_master:
                spinner = Halo(text=colored("Deleting all data...", "red"), spinner=self.dots_, color="red")
                # FIX: catch OS errors when deleting all data
                try:
                    jfile = {}
                    with open(master_file, 'w') as jdata:
                        json.dump(jfile, jdata)
                    with open(filename, 'w') as jdata:
                        json.dump(jfile, jdata)
                    os.remove(filename)
                    os.remove(master_file)
                except OSError as e:
                    logger.error("Failed to delete all data: %s", e)
                    spinner.stop()
                    print(colored("Error: Could not delete all data.", "red"))
                    return
                spinner.stop()
                logger.warning("All data including master password deleted by user.")
            else:
                raise MasterPasswordIncorrect
        elif os.path.isfile(master_file) and not os.path.isfile(filename):
            if stored_master == entered_master:
                spinner = Halo(text=colored("Deleting all data...", "red"), spinner=self.dots_, color="red")
                try:
                    jfile = {}
                    with open(master_file, 'w') as jdata:
                        json.dump(jfile, jdata)
                    os.remove(master_file)
                except OSError as e:
                    logger.error("Failed to delete master password file: %s", e)
                    spinner.stop()
                    print(colored("Error: Could not delete master password file.", "red"))
                    return
                spinner.stop()
                logger.warning("Master password file deleted by user.")
            else:
                raise MasterPasswordIncorrect
