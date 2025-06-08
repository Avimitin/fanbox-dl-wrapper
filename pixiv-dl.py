#!/usr/bin/env python3

import sqlite3
import os
import configparser
import subprocess
import sys


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
    blacklist = set(["--cookie", "--sess-id"])
    args = set(sys.argv)
    if bool(blacklist & args):
        print(f"This wrapper already handle: {", ".join(blacklist)}")
        exit(1)

    profile_parser = FirefoxDefaultProfileParser()
    db_path = profile_parser.get_file("cookies.sqlite")
    db = FireFoxDB(db_path)
    cookies = db.find_fanbox_cookie()

    commands = [
        "fanbox-dl",
        "--cookie",
        ";".join(cookies),
    ] + sys.argv[1:]
    print(f"running {" ".join(commands)}")
    subprocess.run(commands)


if __name__ == "__main__":
    main()
