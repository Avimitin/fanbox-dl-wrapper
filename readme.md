# pixiv-dl.py: fanbox-dl wrapper

`fanbox-dl` is a great tool to download pixiv fanbox images.
It requires session ID or cookies to download the image.
But as fanbox add CloudFlare Verification, copy-paste fanbox session id is not enough
for user who doesn't have Japanese IP. The `cf_clearance` section is also required to bypass the check page.

I've try some cookie exporter, but none of them have great support to re-format cookie output.
And copy-pasting cookie from browser is not that elegant and convinient.
Even with cookies, I've still met HTTP 403 error. It turns out that CloudFlare data contains UA information.

So I write this wrapper to extract cookie and User-Agent from Firefox and feed `fanbox-dl` before it starts.

> Script only support Firefox now.

## Usage

> I don't know the minimum Python 3 version but I am now using Python 3.13.2.

```bash
./pixiv-dl.py <fanbox-dl-argument>
```

## Config

This script support reading creators from toml file. Read [`./fanbox.toml`](./fanbox.toml) for more.

## Strategy

This script will try to find Firefox default profile and read cookies from its database,
then feed the cookie in `fanbox-dl` desired format.

For UA, this script will start a simple http server and use Firefox to send a HTTP request,
so I can get the actual User-Agent that a user will send to Fanbox.

## Limitation

- Firefox headless mode will not exit gracefully, sending termination signal
will cause Firefox try restore latest session.
