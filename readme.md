<h1 align="center">Watercolor</h1>

<p align="center">Click linux desktop gui elements by dictating a label </p>

## Setup

_Note: This repository is a work in progress_

1. Clone this repo into your Talon user directory
2. Install the `python3-pyatspi` package
   - (may be named different depending on your package manager)
3. Run `make run` to run the at-spi server.
4. Launch Talon
5. Say `color toggle` to add colored hats over a11y elements
6. Say `click <watercolor_hint>` to navigate the desktop

## Caveats

- Many application don't implement atspi properly
- Some applications **need to be launched after our atspi client is initialized**

## Support

I offer accessibility software consulting services. Please [reach out to me](https://colton.place/contact/) if you have a question about Talon, screen readers, front-end design, atspi, or any other accessibility software.
