![Tests](https://github.com/colin-nolan/remote-eink/actions/workflows/main.yml/badge.svg)
[![Code Coverage](https://codecov.io/gh/colin-nolan/remote-eink/branch/master/graph/badge.svg)](https://codecov.io/gh/colin-nolan/remote-eink)

# Remote eInk
_A server that can be used to remotely control a display, such as eink screen._

## OpenAPI
The OpenAPI specification can be viewed here:
[https://colin-nolan.github.io/remote-eink/swagger-ui/](https://colin-nolan.github.io/remote-eink/swagger-ui/)


## Troubleshooting
### RPi.GPIO gcc10 issue
A generic error when compiling [RPi.GPIO](https://pypi.org/project/RPi.GPIO/) may be
[caused by a change in gcc10](https://forum.manjaro.org/t/pip-install-rpi-gpio-fail/25788/5):
``` 
collect2: error: ld returned 1 exit status
error: command '/usr/bin/arm-linux-gnueabihf-gcc' failed with exit code 1
```
It can be avoided by setting `CFLAGS`, e.g.:
```
CFLAGS="-fcommon" poetry install
```


## Development
### Implementation
`FlaskApp` app:
- Takes multiple `DisplayController` instances.
- Is associated to `AppData`.
- `AppData` stores the `DisplayController` instances. It provides a `CommunicationPipe` through which write operations
  to the data _must_ be made in requests (as requests may be handled by different processes). 

`Server`:
- Operates a `FlaskApp` app.
- Can be used with `run` (blocking) or `start` (non-blocking).

A `DisplayController`:
- Controls the display of an `Image` within a `ImageStore` using a `DisplayDriver`. 
- Knows what the `current_image` being displayed is.
- May apply transformations to the image using `ImageTransformerSequence`.
- Has `ListenableDisplayController`, `CyclableDisplayController`, and `SleepyDisplayController`
  variants.

An `Image`:
- Allows access to data representing an image.
- Is of a particular type (e.g. `png`).

An `ImageTransformer`:
- Takes an `Image` and modifies it to produce a variation (e.g. a rotated copy of the image).
- Multiple transformers can be put together using an `ImageTransformerSequence`.
- Applied to all images (e.g. when display is rotated, all images can be rotated).

A `DisplayDriver`:
- A driver for a display device.
- Can set an image to be displayed; clear the display; sleep/wake the display.


## Legal
[AGPL v3.0](LICENSE). Copyright 2020, 2021, 2022 Colin Nolan.

This work is in no way related to the company that I work for.
