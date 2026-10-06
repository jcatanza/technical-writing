# Fonts

The banner embeds two fonts. Both are unmodified files from the Google Fonts web service, and both are under the SIL Open Font License 1.1. This folder holds each license text as `OFL-<family>.txt`.

| File | Family | Copyright holder | Source | SHA-256 checksum |
|---|---|---|---|---|
| `PatrickHand-Regular.ttf` | Patrick Hand, version 1.003 | Patrick Wagesreiter | `https://fonts.gstatic.com/s/patrickhand/v25/LDI1apSQOAYtSuYWp8ZhfYeMWQ.ttf` | `8a384204c8ab3e9ed82954d46d8110a66fb5d7acf8f6b64c6f3980c1d0c01993` |
| `CaveatBrush-Regular.ttf` | Caveat Brush, version 1.096 | Google Inc. | `https://fonts.gstatic.com/s/caveatbrush/v12/EYq0maZfwr9S9-ETZc3fKXtMWw.ttf` | `719563de0b82980a30f998539ab14a8a0521b3d70a622aa7d2374b2f8d1c9386` |

These files differ from the ones in the `google/fonts` repository on GitHub. If you swap a font, the drawing changes. Then run `make_banner.py` and `render_png.py` again, as the main README describes.
