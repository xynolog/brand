# brand

Xynolog's mark, wordmarks and typeface, and every icon made from them. The
website, the desktop app and the Browser image pin this repository as a git
submodule at `brand/` and use its files where they are. None of them keeps a
copy.

| Path | What it is | Written by |
|---|---|---|
| `src/mark.svg` | The mark: selection corners around a point, on the dark tile. The one drawing every icon comes from | Hand |
| `favicons/` | `favicon.svg`, `favicon.ico`, PNGs from 16 to 128 px, `apple-touch-icon.png` (square tile), the Android icons and `site.webmanifest` | `generate.sh` |
| `app-icon/` | The desktop app icon on Apple's 824-in-1024 grid: `app-icon.svg`, `icon.png` (1024 px), `icon.icns` and `icon.ico` | `generate.sh` |
| `wordmarks/` | The XYNOLOG wordmark for dark, light and either background, as paths | Hand |
| `fonts/` | Orbitron and its SIL Open Font License | Upstream |

All of it except `fonts/` is Xynolog's, all rights reserved (`LICENSE`).

## Changing the mark

Edit `src/mark.svg`, keeping its `0 0 64 64` viewBox and its
`<rect id="tile">`, then write the derivatives again:

```bash
./generate.sh
```

It runs `generate.py` with `rsvg-convert` in a Debian image pinned by digest,
whose packages come from the Debian snapshot that image was built from, under
Apple `container`, Docker or Podman (`build-tools/container-runtime.sh`).
It writes `favicons/` and `app-icon/` whole. Commit them with the source; CI
writes them again and fails if any byte differs. A consumer takes the new
artwork by moving its `brand` pin.
