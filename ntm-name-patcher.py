#!/usr/bin/env python3

import argparse
import json
import random
import sys
from collections import Counter

OFFSETS = {
    "PLAYERNAMES":       int("0x001838f2", 16),
    "PLAYER2OFFSET1":    int("0x001838f0", 16),
    "PLAYER2OFFSET2":    int("0x00183aa0", 16),
    "TITLESCREEN":       int("0x0017f922", 16),
    "COURSEPOINTERS":    int("0x00183352", 16) + 4, # move to second pointer
    "NAMEPOINTER_START": int("0x00183362", 16), # first name pointer; should start 16 bytes after COURSEPOINTERS
    "NAMESTRINGS_START": int("0x00183552", 16)  # first string start; should start 496 bytes after NAMEPOINTER_START
}

NAMEPOINTER_START = b"\x00\x08\x33\x62"
NAMESTRINGS_START = b"\x00\x08\x35\x52"

DEFAULT_NAMES = [
    "PERSHING", "SIMPSON", "COLT", "GAMOW", "TANGUY",
    "MACNAMARA", "BURBANK", "HANKINS", "CARNEGIE", "MENDENHALL",
    "KUSCH", "SINCLAIR", "GIDDINGS", "AGASSIZ", "WEAVER",
    "JEFFERSON", "DANILOVA", "SAROYAN", "LANGLEY", "COMPTON",
    "RUTH", "ARNOLD", "VAN LOON", "FLANAGAN", "NIMITZ",
    "DAVIS", "CHANDLER", "WILLIAMS", "MACLURE", "KIRK",
    "OGBURN", "TYNDALL", "OWEN", "GIRTIN", "CARLYLE",
    "HARVEY", "DOYLE", "BYRON", "PUSEY", "JENNER",
    "ALBERTZ", "WEBERN", "KIRCHHOFF", "STEINTHAL", "TIRPITZ",
    "DOPPLER", "HEIDEGGER", "ESPINEL", "SARMIENTO", "LOS RIOS",
    "BAROJA", "BALBOA", "ANTOINE", "VINCENT", "CALNOT",
    "SAND", "DEBUSSY", "VALIGNIANI", "GADOLIN", "KIVI",
    "SENGHOR", "DE SITTER", "HILLARY", "SANDERSON", "HYNDMAN",
    "FOWLER", "POWELL", "WEBB", "BAXTER", "STEPHENSON",
    "SMIRKE", "HARDINGE", "ELIOT", "KEAN", "THORPE",
    "DARWIN", "PIRKIN", "WELLS", "SENIOR", "BALFOUR",
    "KNOTT", "NORTH", "CAMPBELL", "THATCHER", "CHAMBERLAIN",
    "BEARDSLEY", "KAYBANDA", "NYERERE", "HASSAN", "BANDA",
    "SABRI", "GHARI", "KIMBANGU", "YAMAMOTO", "DATE",
    "YUKAWA", "HASHIMOTO", "ONO", "FUJIMORI", "KAIEDA",
    "TAKEDA", "MIFUNE", "KUROSAWA", "SAKAMOTO", "SHIMADA",
    "TEZUKA", "LEE", "AN", "WEI", "YANG",
    "HUA", "HAN", "CHOU", "KIM", "PAK",
    "NGUYEN", "NEHRU", "MURAD", "PANDIT", "KAWAKIBI",
    "QUWWATLI", "SAUUMA", "ERMAK", "YESUGAI"
]

def prepString(data: str, len: int, center: bool = False) -> bytes:
    """ Prep string for writing
        - leading/trailing white spaces
        - truncate to len
        - center string in buffer with spaces
        - byteswap
    """
    data = data.strip()[:len]
    if center:
        data = data.center(len)
    else:
        data = data.ljust(len)
    return byteswap(data.encode())


def prepLeaderboardNames(names: list[str]) -> list[str]:
    cleanNames = []
    for name in names:
        cleanNames.append(name.strip()[:12])
    return cleanNames

def buildLeaderboardByteSwapped(names: list[str]) -> bytes:
    # Join as a single Byte string
    namesBytes = b"\xfe".join(name.encode() for name in names)

    # add terminator for final name in the list
    namesBytes += b"\xfe"

    # add an extra byte so byteswap succeeds
    if 1 == len(namesBytes) % 2:
        namesBytes += b"\xfe"
    return byteswap(namesBytes)

def buildLeaderboardPtrs(names: list[str]) -> list[int]:
    # for N > 1, offset of element N == offset of N-1 + len(N-1) + 1
    # offset of element 0 == NAMESTRINGS_START
    namePtrs = [int.from_bytes(NAMESTRINGS_START)]
    for n, _ in enumerate(names, start=1):
        namePtrs.append(len(names[n-1]) + namePtrs[n-1] + 1)

    # 32nd doesn't matter because all leaderboards are using the same pointer
    return namePtrs[0:31]

def encodePlayerNames(p1: str, p2: str) -> bytes:
    """Returns byteswapped names with '\xfe' ready for writing"""
    return byteswap(p1.strip()[:12].ljust(12).encode()
                    + b"\xfe"
                    + p2.strip()[:12].ljust(12).encode()
                    + b"\xfe")

def byteswap(data: bytes, word_size: int=2) -> bytes:
    """
    Reverse the byte order within each word. ChatGPT shat this one out.
    """
    if word_size <= 0:
        raise ValueError("word_size must be positive")
    if len(data) % word_size:
        raise ValueError("data length must be a multiple of word_size")

    return b"".join(
        data[i:i + word_size][::-1]
        for i in range(0, len(data), word_size)
    )

def writeIpsPatch(filename: str, data: list):
    with open(filename, "w+b") as file:
        # PATCH header
        file.write(b"PATCH")

        if "title" in data:
            # title screen
            file.write(OFFSETS["TITLESCREEN"].to_bytes(3))
            file.write(b"\x00\x18") # 24
            file.write(prepString(data["title"], 24, True))

        if "cpu" in data:
            # course name pointers
            file.write(OFFSETS["COURSEPOINTERS"].to_bytes(3))
            file.write(b"\x00\x0c") # 12

            # points all courses to USA's name pointer "$83362", i.e., (08 00 62 33)
            file.write(byteswap(NAMEPOINTER_START))
            file.write(byteswap(NAMEPOINTER_START))
            file.write(byteswap(NAMEPOINTER_START))

        # always update player names
        # update player2 name start offset assuming P1 is 12 bytes long
        # lazy, but it's fine
        file.write(OFFSETS["PLAYER2OFFSET1"].to_bytes(3))
        file.write(b"\x00\x01") # 1
        file.write(b"\xff")
        file.write(OFFSETS["PLAYER2OFFSET2"].to_bytes(3))
        file.write(b"\x00\x01") # 1
        file.write(b"\xff")

        # write player names
        file.write(OFFSETS["PLAYERNAMES"].to_bytes(3))
        file.write(b"\x00\x1a") # 26
        file.write(encodePlayerNames(data["player1"], data["player2"]))

        # write CPU leaderboard names
        if "cpu" in data:
            cleanNames = prepLeaderboardNames(data["cpu"])
            namePtrs = buildLeaderboardPtrs(cleanNames)

            # write leaderboard pointers
            file.write(OFFSETS["NAMEPOINTER_START"].to_bytes(3))
            file.write(b"\x00\x7c") # 124
            file.writelines(byteswap(int(ptr).to_bytes(4)) for ptr in namePtrs)

            byteSwappedNames = buildLeaderboardByteSwapped(cleanNames)

            # write leaderboard names
            file.write(OFFSETS["NAMESTRINGS_START"].to_bytes(3))
            file.write(len(byteSwappedNames).to_bytes(2))
            file.write(byteSwappedNames)

        # EOF footer
        file.write(b"EOF")

def readInput(filename: str) -> list:
    inputs = {
                "player1": "PLAYER 1",
                "player2": "PLAYER 2"
            }
    try:
        with open(filename, "r") as file:
            data = json.load(file)

            if "title" in data and isinstance(data["title"], str):
                inputs["title"] = data["title"]
                print (f"++ Setting title copyright to [{inputs["title"]}]")
            else:
                print ("-- Skipping title screen change")

            if "player1" in data and isinstance(data["player1"], str):
                inputs["player1"] = data["player1"]
                print (f"++ Setting P1 name to [{inputs["player1"] }]")
            else:
                print ("-- Default P1 name to [PLAYER 1]")

            if "player2" in data and isinstance(data["player2"], str):
                inputs["player2"] = data["player2"]
                print (f"++ Setting P2 name to [{inputs["player2"] }]")
            else:
                print ("-- Default P2 name to [PLAYER 2]")

            if "cpu" in data:
                inputs["cpu"] = list(dict.fromkeys(data["cpu"]))
                dupes = {name for name, count in Counter(data["cpu"]).items() if count > 1}
                length = len(inputs["cpu"])
                print (f"++ Found [{length}] unique CPU names")
                if len(dupes) > 0:
                    print (f"  -- Duplicates found: [{dupes}]")
                if length < 31:
                    print(f"  ++ Adding [{31-length}] names from default list")
                    inputs["cpu"].extend(random.sample(DEFAULT_NAMES, 31-length))
                else:
                    if 31 < length:
                        print(f"  -- Truncating last [{length-31}] names")
            else:
                print ("-- Skipping CPU leaderboard names")

    except FileNotFoundError:
        print(f"Error: [{filename}] file was not found.")
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format in [{filename}].")
        print(f"Error: {e.msg}")
        print(f"Line: {e.lineno}, Column: {e.colno}")

    return inputs

def main():
    parser = argparse.ArgumentParser(
                prog="ntm-name-patcher.py",
                usage="python3 %(prog)s <infile> [-o|--output outfile]",
                description="""Generate an IPS patch 200-p1.p1 that allows custom CPU leaderboard names, player names, and title screen.""",
                add_help=True,
                formatter_class=argparse.RawTextHelpFormatter,
                epilog="""
The input json file should take the following format:
{
    "title": "Title",
    "player1": "P1",
    "player2": "P2",
    "cpu": [
            "john",
            "jacob",
            "mary",
            ...
        ]
}

Notes:
- All strings will be stripped of leading/trailing spaces.
- CPU and Player names will be truncated to 12 characters.
- Title string will be truncated to 24 characters and centered.
- If CPU names exist, all courses will use the same set of names.
- Only the first 31 CPU names will be used.
- If there are less than 31 CPU names, default names will fill the remainder.
""")

    parser.add_argument("infile",
                        type=str,
                        help="Input .json file; see format/example below")
    parser.add_argument("-o", "--outfile",
                        type=str,
                        default="200-p1.p1.ips",
                        help="Name of the IPS patch file\nDefault: '200-p1.p1.ips'")

    if len(sys.argv) < 2:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    data = readInput(args.infile)

    writeIpsPatch(args.outfile, data)

if __name__ == "__main__":
    main()