# ntm-name-patcher

Generate an IPS patch for Neo Turf Masters/Big Tournament Golf to replace title screen string, player names, and CPU leaderboard names.

## Description

Are you tired of seeing SIMPSON, OWEN, CAMPBELL, LEE, et. al. in the leaderboards?  Have you ever wanted to see your name instead of PLAYER 1?  This python script will generate an IPS patch to be applied against `200-p1.p1` (CRC: `28c83048`) with your custom set of names, including replacement of the title screen copyright text ("@ 1996 NAZCA CORPORATION").

## Getting Started

### Dependencies

* python3
* IPS patcher, such as [Rom Patcher JS](https://www.marcrobledo.com/RomPatcher.js/)
* `200-p1.p1` (CRC: `28c83048`) from turmfast MAME ROM
* MAME->.neo converter, such as [lithogen](https://github.com/carmiker/lithogen)

### Executing

```
usage: python3 ntm-name-patcher.py <infile> [-o|--output outfile]

Generate an IPS patch 200-p1.p1 that allows custom CPU leaderboard names, player names, and title screen.

positional arguments:
  infile                Input .json file; see example.json or format below

options:
  -h, --help            show this help message and exit
  -o OUTFILE, --outfile OUTFILE
                        Name of the IPS patch file
                        Default: '200-p1.p1.ips'
```

Example:

```
python3 ntm-name-patcher.py input.json -o mynames.ips
```

### JSON format

```
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
```

Notes
- Non-string values will be ignored.
- All strings will be stripped of leading/trailing spaces.
- CPU and Player names will be truncated to 12 characters.
- Title string will be truncated to 24 characters and centered.
- Only the first 31 CPU names will be used.
- If there are less than 31 CPU names, default names will fill the remainder.

## Implementation Notes
### All courses use the same list of names
Each course has its own set of pointer to the start of its leaderboard names.  For simplicity, all courses get the USA pointer value, i.e. `$83362`, such that only one list of names will be referenced.  The additional benefit to this is that all CPU leaderboard names can be 12 characters.

### Player 1 and Player 2 are always patched
Implementation simplicity.

## Version History

* 0.1
  * Initial Release

## Acknowledgments

* [BTG-Dasm](https://github.com/mountainmanjed/BTG-Dasm): dissasembly of the ROMs by mountainmanjed
* lithyV's breakdown of name storage in Neo Turf Masters NTM Tour discord
