# IBM Plex Sans

Unmodified Regular, Medium and SemiBold TrueType fonts from the official
[IBM Plex repository](https://github.com/IBM/plex), revision
`71f558992315a12ca1f06a2215d57962a1992162`.

Source directory:
[`packages/plex-sans/fonts/complete/ttf`](https://github.com/IBM/plex/tree/71f558992315a12ca1f06a2215d57962a1992162/packages/plex-sans/fonts/complete/ttf).
The upstream [license](LICENSE.txt) is preserved verbatim: SIL Open Font License
1.1, with IBM's copyright and reserved font-name notices. These fonts are bundled
assets, not a dependency on an installed system font.

`assets/ui/b1_theme.tres` uses Regular for body text, Medium for buttons/progress,
and SemiBold for titles. Only these three `.ttf` files are added to the restricted
runner's input allowlist; no font import sidecars are required for a cold stage.
