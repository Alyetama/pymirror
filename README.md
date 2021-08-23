# PyMirror

## Requirements

- [Firefox Browser](https://www.mozilla.org/en-US/firefox/new/) (optional)

## Installation

```bash
$ pip install pymirror
```

## CLI Arguments

```bash
$ pymirror --help
usage: pymirror [-h] -i INPUT [-s {lines,list,markdown,reddit}] [-m] [-n NUMBER]
                [-d] [-c] [-D] [-l] [-e] [-v]

optional arguments:
  -h, --help                            Show this help message and \exit
  -i, --input INPUT                     Path to the input file/folder
  -s, --style {lines,list,markdown,reddit}
                                        Output style (default: lines)
  -m, --more-links                      Use mirrored.to to generate more likes
                                        (default: False)
  -n, --number NUMBER                   Select a specific number of servers to
                                        use (default: max)
  -d, --delete                          Delete the file after the process is
                                        complete (default: False)
  -c, --check-status                    Check the status of the remote servers
                                        (default: False)
  -D, --debug                           Debug
  -l, --log                             Show logs and save it to a file
                                        (default: False)
  -e, --experimental                    Generate even more links (experimental)
                                        (default: False)
  -v, --version                         Show program\'s version number and \exit
```

## Basic Usage

```bash
$ pymirror --input foo.txt
```

## Examaples

1. Upload a file to multiple free hosting services and return the output in a markdown style

```bash
0:00:00 | ~/Desktop  | $ pymirror --input foo.txt --style markdown
Press `CTRL+C` at any time to quit.
───────────────────────────────── Uploading... ─────────────────────────────────
[ OK ] https://file.io/PYovv2JI0I4d
[ OK ] https://gofile.io/d/7QGe8z
[ OK ] https://a.uguu.se/QrGNenpZ.txt
[ OK ] https://transfer.sh/mURd/foo.txt
[ OK ] https://oshi.at/AmzjcK/foo.txt
[ OK ] https://0x0.st/iGzX.txt
[ OK ] https://ttm.sh/uhj.txt
[ OK ] https://temp.sh/mXoSA/foo.txt
[ OK ] https://1.filedit.ch/1/VKoJvyuUgtAXfyKEcC.txt
[ OK ] https://pomf.lain.la/f/ibie9ed.txt
─────────────────────────────────── Results ────────────────────────────────────
- [fileio](https://file.io/PYovv2JI0I4d)
- [gofile](https://gofile.io/d/7QGe8z)
- [uguu](https://a.uguu.se/QrGNenpZ.txt)
- [transfersh](https://transfer.sh/mURd/foo.txt)
- [oshi](https://oshi.at/AmzjcK/foo.txt)
- [0x0](https://0x0.st/iGzX.txt)
- [ttm](https://ttm.sh/uhj.txt)
- [filepush](https://temp.sh/mXoSA/foo.txt)
- [tempsh](https://1.filedit.ch/1/VKoJvyuUgtAXfyKEcC.txt)
- [fileditch](https://pomf.lain.la/f/ibie9ed.txt)
───────────────────────────────────── END ──────────────────────────────────────
```

- View on [asciinema](https://asciinema.org/a/Rg1w7TPrjw9RBi7QTowr9158D?t=3)

2. Use the `--more-links` (`-m`) flag<sup>1</sup> to upload to more hosting services (~ 25 more) utilizing Selenium<sup>
   2</sup>

```bash
0:00:00 | ~/Desktop  | $ pymirror --input foo.txt --style markdown --more-links
Press `CTRL+C` at any time to quit.
───────────────────────────────── Uploading... ─────────────────────────────────
[ OK ] https://file.io/eDZG6VfnDN43
[ OK ] https://gofile.io/d/QFNdfE
[ OK ] https://a.uguu.se/VEuSCRXG.txt
[ OK ] https://transfer.sh/14dUZMm/foo.txt
[ OK ] https://oshi.at/AmzkvT/foo.txt
[ OK ] https://0x0.st/iGzX.txt
[ OK ] https://ttm.sh/uhj.txt
[ OK ] https://temp.sh/bAxUT/foo.txt
[ OK ] https://1.filedit.ch/1/VKoJvyuUgtAXfyKEcC.txt
[ OK ] https://pomf.lain.la/f/ibie9ed.txt
[ OK ] https://usersdrive.com/ma2v4fr181v5
[ OK ] https://anonfiles.com/90Sb27Aau8/foo_txt
[ OK ] https://bayfiles.com/BfS025Acuc/foo_txt
[ OK ] https://1fichier.com/?tao8ogg2lyz3n3zh0psn
[ OK ] https://clicknupload.co/ses53quzv5rb
[ OK ] https://tusfiles.com/sc4vfge39aor
[ OK ] https://download.gg/file-12471936_ffbed313aed67837
[ OK ] https://www.solidfiles.com/v/YLjeg8wM8ZgMV
[ OK ] https://turbobit.net/65h5jggvj1ol.html
[ OK ] https://www42.zippyshare.com/v/9tKGS8qj/file.html
[ OK ] https://files.im/y1667uawdq6t
[ OK ] https://drop.download/6rwa2bjv8x0g
[ OK ] https://www.upload.ee/files/13367614/foo.txt.html
[ OK ] https://www.file-upload.com/308wmzsrs4r4
[ OK ] https://dailyuploads.net/p5vjdxt93hdv
[ OK ] https://uptobox.com/4pugjp1vza19
[ OK ] https://dlupload.com/Download/file/N2VmNDEyNDkt
[ OK ] https://mixdrop.co/f/o73e7316h49wj4
[ OK ] https://megaup.net/Ydcb
...and more!
─────────────────────────────────── Results ────────────────────────────────────
- [file.io](https://file.io/eDZG6VfnDN43)
- [gofile.io](https://gofile.io/d/QFNdfE)
- [uguu.se](https://a.uguu.se/VEuSCRXG.txt)
- [transfer.sh](https://transfer.sh/14dUZMm/foo.txt)
- [oshi.at](https://oshi.at/AmzkvT/foo.txt)
- [0x0.st](https://0x0.st/iGzX.txt)
- [ttm.sh](https://ttm.sh/uhj.txt)
- [temp.sh](https://temp.sh/bAxUT/foo.txt)
- [filedit.ch](https://1.filedit.ch/1/VKoJvyuUgtAXfyKEcC.txt)
- [lain.la](https://pomf.lain.la/f/ibie9ed.txt)
- [usersdrive.com](https://usersdrive.com/ma2v4fr181v5)
- [anonfiles.com](https://anonfiles.com/90Sb27Aau8/foo_txt)
- [bayfiles.com](https://bayfiles.com/BfS025Acuc/foo_txt)
- [1fichier.com](https://1fichier.com/?tao8ogg2lyz3n3zh0psn)
- [clicknupload.co](https://clicknupload.co/ses53quzv5rb)
- [tusfiles.com](https://tusfiles.com/sc4vfge39aor)
- [download.gg](https://download.gg/file-12471936_ffbed313aed67837)
- [solidfiles.com](https://www.solidfiles.com/v/YLjeg8wM8ZgMV)
- [turbobit.net](https://turbobit.net/65h5jggvj1ol.html)
- [zippyshare.com](https://www42.zippyshare.com/v/9tKGS8qj/file.html)
- [files.im](https://files.im/y1667uawdq6t)
- [drop.download](https://drop.download/6rwa2bjv8x0g)
- [upload.ee](https://www.upload.ee/files/13367614/foo.txt.html)
- [file-upload.com](https://www.file-upload.com/308wmzsrs4r4)
- [dailyuploads.net](https://dailyuploads.net/p5vjdxt93hdv)
- [uptobox.com](https://uptobox.com/4pugjp1vza19)
- [dlupload.com](https://dlupload.com/Download/file/N2VmNDEyNDkt)
- [mixdrop.co](https://mixdrop.co/f/o73e7316h49wj4)
- [megaup.net](https://megaup.net/Ydcb)
...and more!
───────────────────────────────────── END ──────────────────────────────────────
```

<sup>1</sup>Requires Firefox<br>
<sup>2</sup>A temporary Gecko driver will be installed automatically if it does not already exist

## To do

- [x] ~~Filter servers by upload limit~~
