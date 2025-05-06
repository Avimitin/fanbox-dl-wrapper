#!/usr/bin/env python3

import sqlite3
import os
import configparser
import subprocess
import sys
import time
import tomllib

import http.server
import threading

USER_AGENT = ""


class SingleRequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        # Capture User-Agent from headers
        user_agent = self.headers.get("User-Agent", "Not specified")
        print(f"Captured User-Agent: {user_agent}")
        global USER_AGENT
        USER_AGENT = user_agent

        # Send response
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Request received. Server shutting down.")
        print("Request received. Server shutting down.")

        # Initiate server shutdown in new thread to avoid deadlock
        threading.Thread(target=self.server.shutdown, daemon=True).start()


class OneshotServer:
    def run_server(self):
        server = http.server.ThreadingHTTPServer(
            ("localhost", 18000), SingleRequestHandler
        )
        server.serve_forever()

    def __init__(self) -> None:
        server_thread = threading.Thread(target=self.run_server, daemon=True)
        server_thread.start()


class OneshotFirefox(threading.Thread):
    def __init__(self):
        self.stdout = None
        self.stderr = None
        threading.Thread.__init__(self)

    def kill(self):
        self.p.terminate()

    def run(self):
        self.p = subprocess.Popen(
            ["firefox", "--no-remote", "--headless", "http://localhost:18000"],
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.stdout, self.stderr = self.p.communicate()


def get_latest_ua():
    _ = OneshotServer()
    firefox = OneshotFirefox()
    firefox.start()

    retry = 0
    max_retry = 5
    while USER_AGENT == "":
        if retry < max_retry:
            time.sleep(1)
            retry += 1
        else:
            break

    assert USER_AGENT != ""

    firefox.kill()
    return USER_AGENT


class FireFoxDB:
    cons: sqlite3.Connection

    def __init__(self, path: str):
        print(f"Using db {path}")
        self.cons = sqlite3.connect(path)

    def find_fanbox_cookie(self):
        cur = self.cons.cursor()
        res = cur.execute(
            "SELECT name,value FROM moz_cookies where host='.fanbox.cc'"
        ).fetchall()
        return [f"{name}={value}" for (name, value) in res]


class FirefoxDefaultProfileParser:
    profile: configparser.ConfigParser
    root: str
    default_profile_path: str | None = None

    def __init__(self) -> None:
        # TODO: configurable
        self.root = os.path.join(os.environ["HOME"], ".mozilla/firefox")

    def get_default(self) -> str:
        if self.default_profile_path is not None:
            return self.default_profile_path

        profile_path = os.path.join(self.root, "profiles.ini")
        assert os.path.exists(profile_path)

        self.profile = configparser.ConfigParser()
        self.profile.read(profile_path)

        section = None
        for key in self.profile.sections():
            if key.startswith("Install"):
                section = key
                break
        if section is None:
            print("no default profile found in firefox")
            exit(1)

        self.default_profile_path = self.profile[section]["Default"]
        return self.default_profile_path

    def get_default_profile_path(self) -> str:
        p = os.path.join(self.root, self.get_default())
        assert os.path.exists(p)
        return p

    def get_file(self, name: str) -> str:
        p = os.path.join(self.get_default_profile_path(), name)
        assert os.path.exists(p)
        return p


def main():
    blacklist = set(["--cookie", "--sess-id", "--user-agent", "--creator"])
    args = set(sys.argv)
    if bool(blacklist & args):
        print(f"This wrapper already handle: {", ".join(blacklist)}")
        exit(1)

    profile_parser = FirefoxDefaultProfileParser()
    db_path = profile_parser.get_file("cookies.sqlite")
    db = FireFoxDB(db_path)
    cookies = db.find_fanbox_cookie()
    ua = get_latest_ua()

    options = None
    with open("fanbox.toml", "rb") as f:
        data = tomllib.load(f)
        options = data["options"]

    commands = [
        "fanbox-dl",
        "--user-agent",
        ua,
        "--cookie",
        ";".join(cookies),
        "--creator",
        ",".join(options["creators"]),
    ] + sys.argv[1:]
    print(f"running {" ".join(commands)}")
    subprocess.run(commands)


if __name__ == "__main__":
    main()
