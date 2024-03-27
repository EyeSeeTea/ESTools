# Catalina log notificator script

## Description

The script is used to identify the date when an error occurs in the catalina.out log and notify it to the MS Teams channel.

## Usage

It is executed like this:

```bash
usr/bin/python3 /home/tomcatuser/bin/log_notificator/log_notificator.py /home/tomcatuser/bin/log_notificator/config.json
```

## Configuration

The config file contains the following fields:

- `"log_path"`: It's the absolute path to catalina.out.
- `"log_string"`: "Error while sending email: Sending the email to the following server failed", it's the error to search for.
- `"ms_url"`: It's the URL for sending messages to MS Teams.
- `"control_file"`: It's the absolute path to the control file (it needs to be created with a touch command).
- `"notification_script_test"`: It's the absolute path to a Ruby version for testing that the parameters work correctly and to preview them before sending to the Teams channel.
- `"notification_script_path"`: It's the absolute path to the Ruby script that notifies Teams.
