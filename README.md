# rpi-auto-voice-recorder

This is a tool for automatic recording, processing and uploading of voice (e.g. sermons, talks, lectures, etc.) to be used on a device like Raspberry Pi.

# start recording on reboot

You can do so with `crontab -e`, by appending this line:

```shell
@reboot screen -md sh /path/to/your/script.sh
```

Respectively, `/path/to/your/script.sh` can look as follows:

```shell
#!/bin/sh

cd rpi-auto-voice-recorder
./record_next.py -i recording_times.json -c 2 -d 1
```
