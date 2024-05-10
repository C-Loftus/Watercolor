# Watercolor

## Setup

This repo has an atspi server that gets a11y element names and positions, and then a Talon client that creates hats for user interaction using them.

1. Clone this repo into your user directory
2. Install `python3-pyatspi` (may be named different depending on your package manager)
3. Run `make run` to run the at-spi server.
   1. The server can also be ran within your user directory since the [.create_coords.py](.atspi-server/create_coords.py) is named with a `.` at the start so it is ignored by Talon
4. Launch Talon, it should paint every element with a hat

## Notes / Caveats

- **This repo is a work in progress**
- Many apps don't implement at-spi properly
  - Try to use well supported common applications like Visual Studio Code, Firefox, etc.
  - Please submit upstream a11y requests to those applications
- Some applications **need to be launched after our atspi is initialized**
  - Firefox is one notable example
