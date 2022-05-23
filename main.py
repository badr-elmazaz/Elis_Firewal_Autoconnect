import hashlib
import os
import platform
import subprocess
import sys
import time
from dataclasses import dataclass
from threading import Thread
from tkinter import *
from tkinter import messagebox
from typing import Optional
from urllib.parse import urlparse
import notifypy
import requests
import schedule
import ujson
import win32com.client
import winshell
from PIL import ImageTk, Image, ImageSequence
from cryptography.fernet import Fernet
import logging


# todo list:
# - add doc in functions
# - add doc in classes
# - optimize code
# - add comment
# - add accept privacy policy
# - multi language
APP_NAME = "Eli$ Firewall Autoconnect"
ICON = os.path.join(os.getcwd(), "assets", "main_icon.ico")
KEY = "o0kTrnAyS63ANFwT6wXC16BErGzbbkFDOrKbQFuNEXg="
NOTIFICATION_ICON = ICON
logging.basicConfig(level=logging.INFO, filename="log.log", format="%(asctime)s - %(levelname)s - %(message)s")


class Consts():
    # colors
    OFF_WHITE = '#fffffe'
    DARK_BLUE = '#232946'
    PINK = "#eebbc3"
    # wifi
    SSID = "ELIS.org Studenti"


@dataclass
class HackFireWall():
    username: Optional[str] = None
    password: Optional[str] = None
    token: Optional[str] = None
    portal: Optional[str] = None
    session = requests.Session()
    SUCCEED = 1
    FAILED = 0
    ERROR = 2
    root: Tk = Tk()
    URL: Optional[str] = "http://gtatic.com/generate_204"
    privacy_check_box = IntVar()
    notification = notifypy.Notify()
    frame: Optional[Frame] = None
    remember_credentials_check_box = IntVar()
    CONFIG: dict = None
    OS = platform.system().lower()
    ON_SSID = False
    TIMEOUT = 10
    username_entry = None
    password_entry = None
    robot_entry = None
    checkbox_start_with_os = IntVar()
    checkbox_show_notifications = IntVar()
    fernet = Fernet(KEY)
    checkbox_robot_verification = IntVar()

    def _get_sha_256(self, s: str):
        return hashlib.sha256(s.encode('utf-8')).hexdigest()

    # todo compolete here
    def _validate_OS(self):
        if self.OS == "windows":
            return True

    def _send_notification(self, status):
        self.notification.icon = NOTIFICATION_ICON
        self.notification.application_name = APP_NAME
        if self.CONFIG["app"]["show_notifications"]:
            if status == self.SUCCEED:
                self.notification.title = "Logged in successfully"
                self.notification.message = "Now you are connected to the internet, not at all, I suggest to use a VPN to bypass limitations"
            elif status == self.FAILED:
                self.notification.title = "Login Failed"
                self.notification.message = "Wrong credentials"
            elif status == self.ERROR:
                self.notification.title = "Error"
                self.notification.message = "Generic error, contact the developer"
            self.notification.send()

    def _ssid_schedule(self):
        if self._is_connected_to_SSID() and not self._is_there_internet_connection():
            logging.info("I'm logging in")
            status_login = self._login()
            if status_login == self.SUCCEED:
                self._send_notification(self.SUCCEED)
            if status_login == self.FAILED:
                self._send_notification(self.FAILED)
            if status_login == self.ERROR:
                self._send_notification(self.ERROR)

    def _encrypt_dict(self, d: dict):
        binary_dict = ujson.dumps(d, indent=2).encode('utf-8')
        encrypted = self.fernet.encrypt(binary_dict)
        return encrypted

    def _decrypt_dict(self, d: bytes):
        decrypted = self.fernet.decrypt(d)
        dict = ujson.loads(decrypted.decode("utf-8"))
        return dict

    def _update_config(self):
        config_to_save = {k: self.CONFIG[k] for k in self.CONFIG if k != "user"}
        with open("config.json", "w") as f:
            ujson.dump(config_to_save, f, indent=4)
        encrypted_data = self._encrypt_dict(self.CONFIG["user"])
        with open("data", "wb") as f:
            f.write(encrypted_data)

    def _robot_button_clicked(self):
        ans = self.robot_entry.get().lower().strip()
        if not ans:
            ans = ""
        ans_hashed = self._get_sha_256(ans)
        if ans_hashed == self.CONFIG["app"]["robot"]:
            logging.info("correct answer")
            self._create_main_gui()
            return
        logging.info("not correct answer")
        messagebox.showerror("Error", "Answer is note corrct")
        self.start()

    def _gui_you_are_not_a_robot(self):
        self.root.title("You are not a robot")
        self.root.geometry("400x200")
        self.root.iconbitmap(ICON)
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.root.config(bg=Consts.DARK_BLUE)

        Label(self.root, text="Who was in Paris?", bg=Consts.DARK_BLUE, fg=Consts.OFF_WHITE,
              font=("Helvetica", 11, "bold")).place(x=135, y=10)

        self.robot_entry = Entry(self.root, highlightthickness=0, relief=FLAT, bg=Consts.DARK_BLUE,
                                 fg=Consts.OFF_WHITE,
                                 font=("Helvetica", 11))
        self.robot_entry.place(x=80, y=75)
        robot_line = Canvas(self.root, width=250, height=2.3, bg=Consts.PINK, highlightthickness=0, relief=FLAT)
        robot_line.place(x=80, y=95)
        button = Button(self.root, text="I'm not a robot", width=15, height=2,
                        cursor="hand2",
                        font=("Helvetica", 10, "bold"), bd=0, command=lambda: self._robot_button_clicked())
        button.place(x=135, y=140)
        button.config(bg=Consts.PINK, fg=Consts.DARK_BLUE)

    def _set_config(self):
        with open("config.json", "r") as f:
            self.CONFIG = ujson.load(f)
        with open("data", "rb") as f:
            encrypted_data = f.read()
        decrypted_data = self._decrypt_dict(encrypted_data)
        self.CONFIG["user"] = decrypted_data

    def _verify_if_start_gui(self):
        if not self.CONFIG["user"]["username"] or not self.CONFIG["user"]["password"]:
            return True
        if not self.CONFIG["app"]["remember_credentials"]:
            return True
        return False

    def _start_routine(self):
        while True:
            self._ssid_schedule()
            time.sleep(3)
        # schedule.every(2).seconds.do(self._ssid_schedule)
        # self._start_schedule()

    def _manage_start_with_os(self, start: bool):
        startup_path = winshell.startup()
        full_path = os.path.join(startup_path, APP_NAME + ".lnk")
        if start:
            # if not
            if not os.path.exists(full_path):
                logging.info(("Im setting startup shortcut"))
                self._create_shortcut(program_path=__file__, shortcut_icon_path=ICON, shortcut_path=full_path)
        else:
            if os.path.exists(full_path):
                try:
                    logging.info(("Im removing startup shortcut"))
                    os.remove(full_path)
                except Exception as e:
                    logging.exception("Error removing shortcut")

    def _manage_gui_settings_button(self, top):
        self.CONFIG["app"]["remember_credentials"] = self.remember_credentials_check_box.get() == 1
        if "windows" in self.OS:
            self.CONFIG["app"]["start_with_os"] = self.checkbox_start_with_os.get() == 1
            self._manage_start_with_os(self.CONFIG["app"]["start_with_os"])
        else:
            self.CONFIG["app"]["start_with_os"] = False
        self.CONFIG["app"]["show_notifications"] = self.checkbox_show_notifications.get() == 1
        self.CONFIG["app"]["start_robot"] = self.checkbox_robot_verification.get() == 1
        self._update_config()
        top.destroy()

    def _set_all_settings_checkboxes_default_values(self):
        if self.CONFIG["app"]["remember_credentials"]:
            self.remember_credentials_check_box.set(1)
        if self.CONFIG["app"]["start_with_os"]:
            self.checkbox_start_with_os.set(1)
        if self.CONFIG["app"]["show_notifications"]:
            self.checkbox_show_notifications.set(1)

    def _gui_settings(self):
        # self.root.withdraw()
        top = Toplevel(self.root)
        top.title("Settings")
        top.geometry("350x220")
        top.resizable(False, False)
        top.config(bg=Consts.DARK_BLUE)
        self._set_all_settings_checkboxes_default_values()
        Label(top, text="Remember Credentials", bg=Consts.DARK_BLUE, fg=Consts.PINK,
              font=("Helvetica", 10, "bold")).place(x=50, y=10)

        checkbox_remember_credentials = Checkbutton(top, text="",
                                                    variable=self.remember_credentials_check_box, bg=Consts.DARK_BLUE)
        checkbox_remember_credentials.place(x=20, y=10)
        # todo implement also for other os
        if "windows" in self.OS:
            Label(top, text="Start with OS", bg=Consts.DARK_BLUE, fg=Consts.PINK,
                  font=("Helvetica", 10, "bold")).place(x=50, y=50)
            checkbox_start_with_os = Checkbutton(top, text="",
                                                 variable=self.checkbox_start_with_os, bg=Consts.DARK_BLUE)
            checkbox_start_with_os.place(x=20, y=50)
        Label(top, text="Show Notifications", bg=Consts.DARK_BLUE, fg=Consts.PINK,
              font=("Helvetica", 10, "bold")).place(x=50, y=90)
        checkbox_show_notifications = Checkbutton(top, text="",
                                                  variable=self.checkbox_show_notifications, bg=Consts.DARK_BLUE)
        checkbox_show_notifications.place(x=20, y=90)
        Label(top, text="Start robot verification", bg=Consts.DARK_BLUE, fg=Consts.PINK,
              font=("Helvetica", 10, "bold")).place(x=50, y=130)
        checkbox_robot= Checkbutton(top, text="",
                                                  variable=self.checkbox_robot_verification, bg=Consts.DARK_BLUE)
        checkbox_robot.place(x=20, y=130)
        if self.CONFIG["app"]["start_robot"]:
            checkbox_robot.select()
        if self.CONFIG["app"]["remember_credentials"]:
            checkbox_remember_credentials.select()
        if "windows" in self.OS:
            if self.CONFIG["app"]["start_with_os"]:
                checkbox_start_with_os.select()
        if self.CONFIG["app"]["show_notifications"]:
            checkbox_show_notifications.select()
        button = Button(top, width=14, height=1, text="Save",
                        command=lambda: self._manage_gui_settings_button(top), bg=Consts.PINK, fg=Consts.DARK_BLUE,
                        font=("Helvetica", 10, "bold"))
        # button.place(x=700, y=350)
        button.place(x=120, y=170)

    def _gui_you_are_not_connected_to_SSID(self):
        self.root.title("Not connected")
        self.root.geometry("881x482")
        self.root.iconbitmap(ICON)
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        # self.root.config(bg=Consts.DARK_BLUE)
        not_connected_png = Image.open("assets/not_connected.png")
        not_connected_png_tk = ImageTk.PhotoImage(not_connected_png.resize((800, 400), Image.Resampling.LANCZOS))
        label = Label(self.root, image=not_connected_png_tk)
        label.place(x=40.5, y=60)
        label.image = not_connected_png_tk
        label_2 = Label(self.root, text="You are not connected to the correct SSID", font=("Helvetica", 20),
                        fg=Consts.PINK)
        label_2.place(x=240, y=10)
        button = Button(self.root, width=15, height=2, text="I'm connected",
                        command=self._manage_gui_connect_to_ssid_button, bg=Consts.PINK, fg="white")
        button.place(x=700, y=400)

    def _manage_gui_connect_to_ssid_button(self):
        self.root.destroy()
        self.root = Tk()
        self.start()

    def _gui_already_connected(self):
        self.root.title("Already connected")
        self.root.geometry("700x200")
        self.root.iconbitmap(ICON)
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.root.config(bg=Consts.DARK_BLUE)
        label_2 = Label(self.root, text="You are already connected to the correct SSID and logged in to the firewall", font=("Helvetica", 13),
                        fg=Consts.PINK, bg=Consts.DARK_BLUE)
        label_2.place(x=50, y=20)
        button = Button(self.root, width=15, height=2, text="OK",
                        command=lambda: self.root.destroy(), bg=Consts.PINK, fg="white")
        button.place(x=300, y=100)


    def start(self):
        self._set_config()
        if not self._is_connected_to_SSID():
            # if True:
            logging.info("you are not connected to the ssid")
            self._gui_you_are_not_connected_to_SSID()
            self.root.mainloop()
            return
        elif self._is_there_internet_connection():
            logging.info("you are already connected to the ssid")
            self._gui_already_connected()
            self.root.mainloop()
            return
        if self._verify_if_start_gui():
            logging.info("Im creating main gui")
            if self.CONFIG["app"]["start_robot"]:
                self._gui_you_are_not_a_robot()
            else:
                print("main gui")
                self._create_main_gui()
            self.root.mainloop()
        else:
            print(f"here, {self.CONFIG}")
            self.username = self.CONFIG["user"]["username"]
            self.password = self.CONFIG["user"]["password"]
            # todo manage status code returned
            status_login = self._login()
            self._send_notification(status_login)
            self._start_routine()

    def _play_gif(self):
        gif = Image.open("assets/pc.gif")
        label = Label(self.root)
        label.pack(side=LEFT)
        while True:
            for img in ImageSequence.Iterator(gif):
                img = ImageTk.PhotoImage(img)
                label.config(image=img)
                self.root.update()
                time.sleep(0.06)

    def _play_first_gif(self):
        gif = Image.open("assets/privacy.gif")
        label = Label(self.frame)
        label.pack(side=LEFT)
        while True:
            for img in ImageSequence.Iterator(gif):
                img = ImageTk.PhotoImage(img)
                label.config(image=img)
                self.root.update()
                time.sleep(0.06)

    def _continue_to_next_gui(self):
        pass

    def _continue_button(self, frame):
        button = Button(frame, width=15, height=2, text="Continue", command=self._continue_to_next_gui, )
        button.grid(row=2, column=0)





    def _on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.root.destroy()
            sys.exit(0)

    def _get_credentials_frame(self):
        gif_thread = Thread(target=self._play_gif)
        gif_thread.daemon = True
        gif_thread.start()
        self._login_gui()

    def _create_main_gui(self):
        self.root.title(APP_NAME)
        self.root.geometry("900x400")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.root.config(bg=Consts.DARK_BLUE)
        self._get_credentials_frame()

    def _validate_and_set_values_in_gui(self):
        # todo complete here
        pass



    def _quit_all(self, top):
        top.destroy()
        self.root.destroy()

    def _loading_window(self):
        self.root.withdraw()
        top = Toplevel(self.root)
        top.title("Loading")
        top.geometry("350x200")
        top.resizable(False, False)
        top.config(bg=Consts.DARK_BLUE)
        label = Label(top, text="Loading...", bg=Consts.DARK_BLUE, fg=Consts.PINK, font=("Helvetica", 13, "bold"))
        label.pack(pady=10)
        top.protocol("WM_DELETE_WINDOW", lambda: self._quit_all(top))
        return top


    # def _start_schedule(self):
    #     while True:
    #         # Checks whether a scheduled task
    #         # is pending to run or not
    #         schedule.run_pending()
    #         time.sleep(1)

    def _manage_succeed_login(self, top_loading_window):
        self._send_notification(self.SUCCEED)
        if self.remember_credentials_check_box.get() == 1:
            self.CONFIG["app"]["remember_credentials"] = True
            self.CONFIG["user"]["username"] = self.username
            self.CONFIG["user"]["password"] = self.password
            self._update_config()
            # todo fix here, not showed this message
        label = Label(top_loading_window, text="Logged in successfully!", bg=Consts.DARK_BLUE, fg=Consts.PINK,
                      font=("Helvetica", 13, "bold"))
        label.pack(pady=10)
        self._start_routine()

    def _manage_failed_login(self, top_loading_window):
        self._send_notification(self.FAILED)
        label = Label(top_loading_window, text="Failed Authentication, retry", bg=Consts.DARK_BLUE, fg=Consts.PINK,
                      font=("Helvetica", 13, "bold"))
        label.pack(pady=10)
        button_retry = Button(top_loading_window, text="Retry", bg=Consts.DARK_BLUE, fg=Consts.PINK,
                              font=("Helvetica", 13, "bold"), command=lambda: self._retry_login(top_loading_window))
        button_retry.pack(pady=10)
        # clean the text input of the user
        self.username_entry.delete(0, 'end')
        self.password_entry.delete(0, 'end')

    def _manage_error_login(self, top_loading_window):
        self._send_notification(self.ERROR)
        label = Label(top_loading_window, text="Generic Error, contact the developer", bg=Consts.DARK_BLUE,
                      fg=Consts.PINK,
                      font=("Helvetica", 13, "bold"))
        label.pack(pady=10)

    def _retry_login(self, top_loading_window):
        top_loading_window.destroy()
        self.root.deiconify()

    def _button_login_clicked(self):
        if not self._check_all_is_ok():
            # todo complete here
            return
        top_loading_window = self._loading_window()
        login_status_code = self._login()
        if login_status_code == self.SUCCEED:
            self._manage_succeed_login(top_loading_window)
        elif login_status_code == self.FAILED:
            self._manage_failed_login(top_loading_window)
        elif login_status_code == self.ERROR:
            self._manage_error_login(top_loading_window)

    def _play_login_button_gif_and_login(self, button, button_gif):
        for img in ImageSequence.Iterator(button_gif):
            img = ImageTk.PhotoImage(img.resize((120, 60), Image.Resampling.LANCZOS))
            button.config(image=img)
            self.root.update()
            time.sleep(0.06)

        img = ImageSequence.Iterator(button_gif)[0]
        img_tk = ImageTk.PhotoImage(img.resize((120, 60), Image.Resampling.LANCZOS))
        button.config(image=img_tk)
        self.root.update()

    def _button_login(self):
        def _hover(e):
            button.config(bg=Consts.OFF_WHITE)
            button.config(fg=Consts.PINK)

        def _leave(e):
            button.config(bg=Consts.PINK)
            button.config(fg=Consts.OFF_WHITE)

        button = Button(self.root, text="Login", width=11, height=2,
                        cursor="hand2",
                        font=("Helvetica", 10, "bold"), bd=0, command=lambda: self._button_login_clicked())
        button.place(x=710, y=330)
        button.config(bg=Consts.PINK, fg=Consts.DARK_BLUE)
        button.bind("<Enter>", _hover)
        button.bind("<Leave>", _leave)

    def _set_password_eye(self, password_entry):
        def show():
            eye_opened_button = Button(self.root, image=eye_opened_tk, cursor="hand2", activebackground="black", bd=0,
                                       command=hide)
            eye_opened_button.place(x=855, y=225)
            eye_opened_button.image = eye_opened_tk
            password_entry.config(show="")

        def hide():
            eye_closed_button = Button(self.root, image=eye_closed_tk, cursor="hand2", activebackground="black", bd=0,
                                       command=show)
            eye_closed_button.place(x=855, y=225)
            eye_closed_button.image = eye_closed_tk
            password_entry.config(show="*")

        eye_opened = Image.open("assets/opened_eye.png").resize((25, 20), Image.Resampling.LANCZOS)
        eye_closed = Image.open("assets/closed_eye.png").resize((25, 20), Image.Resampling.LANCZOS)
        eye_opened_tk = ImageTk.PhotoImage(eye_opened)
        eye_closed_tk = ImageTk.PhotoImage(eye_closed)
        hide()

    def _settings_window(self):
        # todo complete here
        pass

    def _set_settings_icon(self):
        setting_icon = Image.open("assets/settings.png").resize((25, 25), Image.Resampling.LANCZOS)
        setting_icon_tk = ImageTk.PhotoImage(setting_icon)
        settings_button = Button(self.root, image=setting_icon_tk, cursor="hand2", activebackground="black", bd=0,
                                 command=self._gui_settings)
        settings_button.place(x=872, y=0)
        settings_button.image = setting_icon_tk

    def _remember_credentials_checkbox(self):
        c1 = Checkbutton(self.root, text='', variable=self.remember_credentials_check_box, onvalue=1, offvalue=0,
                         relief=FLAT, bg=Consts.DARK_BLUE, fg=Consts.DARK_BLUE, font=("Helvetica", 10, "bold"),
                         activebackground="black")
        c1.place(x=685, y=280)
        Label(self.root, text="Remember Credentials", bg=Consts.DARK_BLUE, fg=Consts.OFF_WHITE,
              font=("Helvetica", 10, "bold")).place(x=705, y=282)

    def _login_gui(self):

        Label(self.root, text="Username", bg=Consts.DARK_BLUE, fg=Consts.OFF_WHITE,
              font=("Helvetica", 11, "bold")).place(x=712, y=68)
        Label(self.root, text="Password", bg=Consts.DARK_BLUE, fg=Consts.OFF_WHITE,
              font=("Helvetica", 11, "bold")).place(x=712, y=188)
        self.username_entry = Entry(self.root, highlightthickness=0, relief=FLAT, bg=Consts.DARK_BLUE,
                                    fg=Consts.OFF_WHITE,
                                    font=("Helvetica", 11))
        self.username_entry.place(x=650, y=100)
        username_line = Canvas(self.root, width=200, height=2.3, bg=Consts.PINK, highlightthickness=0, relief=FLAT)
        username_line.place(x=650, y=130)
        self.password_entry = Entry(self.root, bg=Consts.DARK_BLUE, fg=Consts.OFF_WHITE, relief=FLAT,
                                    font=("Helvetica", 11))
        self.password_entry.config(show="*")
        self.password_entry.place(x=650, y=225)
        password_line = Canvas(self.root, width=200, height=2.3, bg=Consts.PINK, highlightthickness=0, relief=FLAT)
        password_line.place(x=650, y=245)
        self._button_login()
        self._set_password_eye(self.password_entry)
        self._set_settings_icon()
        self._remember_credentials_checkbox()

    def _get_login_payload(self):
        return {
            "user.username": self.username,
            "user.password": self.password,
            "token": [self.token, self.token],
            "portal": self.portal
        }

    def _extract_token_and_portal(self, url: str):
        data = {query.split("=")[0]: query.split("=")[1] for query in urlparse(url).query.split("&")}
        self.token = data.get("token")
        self.portal = data.get("portal")

    def _get_data_for_second_verification(self):
        return {
            "delayToCoA": "0", "coaType": "Reauth", "coaSource": "GUEST",
            "coaReason": "Guest authenticated for network access", "waitForCoA": "true", "portalSessionId": self.portal,
            "token": self.token
        }

    def _get_data_third_post(self):
        return {
            "portalSessionId": self.portal,
            "token": self.token
        }

    def _check_all_is_ok(self) -> bool:
        self.username = self.username_entry.get()
        self.password = self.password_entry.get()
        if not self.username or not self.password:
            messagebox.showinfo("Blank", "You have inserted one or more blank fields")
            return False
        return True

    def _login(self):
        try:
            self.session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36"})
            resp = self.session.get(self.URL, timeout=self.TIMEOUT)
            redirect_location = resp.headers.get("Location")
            self._extract_token_and_portal(redirect_location)
            self.session.cookies.set("token", self.token, path="/portal", domain='ise30-1.elis.org:8443')
            self.session.cookies.set("checkCookiesEnabled", "value", path="/portal", domain='ise30-1.elis.org:8443')
            resp = self.session.get(redirect_location)
            self.token = resp.headers.get("token")
            self.session.cookies.set("APPSESSIONID", resp.headers.get("APPSESSIONID"), path="/portal",
                                     domain='ise30-1.elis.org:8443')
            self.session.cookies.set("token", self.token, path="/portal", domain='ise30-1.elis.org:8443')
            data = self._get_login_payload()
            url_login = "https://ise30-1.elis.org:8443/portal/LoginSubmit.action?from=LOGIN"
            resp = self.session.post(url_login, data=data, timeout=self.TIMEOUT)
            if "autenticazione non riuscita" in resp.text.lower():
                return self.FAILED
            self.portal = resp.cookies.get_dict().get("portalSessionId")
            url_continue = "https://ise30-1.elis.org:8443/portal/Continue.action?from=POST_ACCESS_BANNER"
            # here status code is 500
            resp = self.session.post(url_continue, data={"token": self.token}, timeout=self.TIMEOUT)
            url_do_co_action = "https://ise30-1.elis.org:8443/portal/DoCoA.action"
            self.session.cookies.set("portalSessionId", self.portal, path="/portal", domain='ise30-1.elis.org:8443')
            self.session.cookies.set("token", self.token, path="/portal", domain='ise30-1.elis.org:8443')
            self.session.cookies.set("; checkCookiesEnabled", "value", path="/portal", domain='ise30-1.elis.org:8443')
            self.session.headers.update({"Origin": "https://ise30-1.elis.org:8443/portal/DoCoA.action"})
            self.session.headers.update({"Refer": "https://ise30-1.elis.org:8443/portal/LoginSubmit.action?from=LOGIN"})
            resp = self.session.post(url_do_co_action, data=self._get_data_for_second_verification(),
                                     timeout=self.TIMEOUT)
            third_post_login = "https://ise30-1.elis.org:8443/portal/CheckCoAStatus.action"
            resp = self.session.post(third_post_login, data=self._get_data_third_post(), timeout=self.TIMEOUT)
            self.token = resp.headers.get("token")
            self.session.cookies.set("token", self.token, path="/portal", domain='ise30-1.elis.org:8443')
            self.session.headers.update(
                {"Refer": "https://ise30-1.elis.org:8443/portal/Continue.action?from=POST_ACCESS_BANNER"})
            resp = self.session.post(third_post_login, data=self._get_data_third_post(), timeout=self.TIMEOUT)
            try:
                json_resp = resp.json()
                if json_resp.get("status").lower() == "success" and json_resp.get("messages") == ["complete"]:
                    return self.SUCCEED
                else:
                    return self.ERROR
            except:
                logging.exception("Error in parsing json response")
                return self.ERROR

        except:
            logging.exception("Error in login")
            return self.ERROR

    def _is_connected_to_SSID(self):
        if "windows" in self.OS:
            return Consts.SSID in subprocess.check_output(['netsh', 'WLAN', 'show', 'interfaces']).decode("utf-8",
                                                                                                          errors="ignore")
        if "linux" in self.OS:
            # todo check if it working
            return subprocess.check_output(["sudo", "iwgetid"]).decode("utf-8").split('"')[1].strip()
        if "darwin" in self.OS:
            process = subprocess.Popen(
                ['/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport', '-I'],
                stdout=subprocess.PIPE)
            out, err = process.communicate()
            process.wait()
            return Consts.SSID in out.decode("utf-8")
        return False

    # todo improve this function
    def _is_there_internet_connection(self):
        try:
            resp = requests.get("http://www.google.com", timeout=self.TIMEOUT, allow_redirects=False)
            if "ise30-1.elis.org" in resp.text.lower():
                logging.debug("No internet connection.")
                return False
            logging.debug("Connected to the Internet")
            return True
        except (requests.ConnectionError, requests.Timeout) as exception:
            logging.debug("No internet connection.")
            return False

    def _create_shortcut(self, shortcut_path, shortcut_icon_path, program_path):
        if not shortcut_path.lower().endswith(".lnk"):
            shortcut_path = shortcut_path + ".lnk"
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = program_path
        shortcut.IconLocation = shortcut_icon_path
        shortcut.save()


if __name__ == "__main__":
    HackFireWall().start()
