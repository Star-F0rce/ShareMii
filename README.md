# Tomodachis

A libadwaita / GTK 4 GUI (and CLI) for exporting and importing content from
*Tomodachi Life: Living the Dream* save files.

Tomodachis is a fork of [ShareMii](https://github.com/Star-F0rce/ShareMii) by
**Star-F0rce** and **Ben Rau**. The save-file logic is theirs; this fork swaps
the tkinter front-end for a GTK 4 + libadwaita interface that follows the
[GNOME Human Interface Guidelines](https://developer.gnome.org/hig/).
Distributed under the **GNU GPL v3.0**, same as upstream — see
[LICENSE](LICENSE).

This is specifically meant for Linux users. I recommend Windows and Mac users use the original [ShareMii](https://github.com/Star-F0rce/ShareMii).

## Why?

I recently got into Living The Dream and wanted to import Miis that my friends sent me and then I noticed how bad the Tkinter UI looked on GNOME. There's scaling issues, making text hard to read, UI elements somehow look straight out of the modern WinUI and Win9x at the same time. 

Using the CLI of course is an option, but I really wanted a GUI consistent with my desktop environment, so I thought I'd try considering my first libadwaita app [Mixtapes](https://github.com/m-obeid/Mixtapes) turned out great.

## How do I get this?

Under Releases, you can find an AppImage for Tomodachis.

Alternatively, you can run from source, see below.

## Requirements

- Python 3.10+
- GTK 4 (≥ 4.10) and libadwaita (≥ 1.4)
- PyGObject

On Arch:

```
sudo pacman -S python-gobject gtk4 libadwaita
```

On Debian/Ubuntu:

```
sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1
```

## Usage

Launch the GUI by running with no arguments:

```
python3 Tomodachis.py
```

The CLI is unchanged from upstream:

```
Tomodachis [-h] [-l | -i Mii.ltd | -o Name | -a Directory] [--backup] [save] [slot]
```

- `-l` — List every Mii found in `save`
- `-i Mii.ltd` — Import `Mii.ltd` into `save`, overwriting `slot`
- `-o Name` — Export Mii from `save` at `slot` into `Name.ltd`
- `-a Directory` — Export all Miis to `Directory`
- `--backup` — Create a backup of the save folder before importing


## Credits

Tomodachis is a fork of **ShareMii** by Star-F0rce and Ben Rau.
All the heavy lifting — reverse-engineering the save format and writing the
import/export logic — is theirs. Please send save-format bug reports
upstream when possible: <https://github.com/Star-F0rce/ShareMii>.

## Disclaimer (from upstream)

ShareMii was made by humans, for humans. Please don't feed this work to an AI.
If you want to base your code off this project for another language, that's
fine, but please don't use an AI model to do so.

If your code directly ports how importing/exporting works from this repo, the
upstream authors would appreciate credit for the code; if you just code
support for `.ltd` files, you're free to do whatever you want.

Hold off on writing code that parses `.ltd`s for now — upstream is rewriting
the format to be more compatible with the game's libraries. If you're just
supporting uploads of `.ltd`s, you're fine; there won't be a release of the
new format unless there's a working v3 → v4 conversion.

## License

GNU General Public License v3.0. See [LICENSE](LICENSE).
