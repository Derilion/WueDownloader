### WueCampus Course Updater

A simple script to downloadcurrent course files into a directory

## Setup
Install required files from requirements.txt and configure config.ini. Parameters are:
1. User: the sibboleth user, like s999999
2. Password: the user password
3. BaseURL: usually just https://wuecampus2.uni-wuerzburg.de
4. TargetDir: directory where the files should be downloaded to
5. Interval: seconds between attempts to download data
6. LogPath: Name of the logfile

## Usage
Start the script as a background job like:
```console
foo@bar:~$ nohup main.py
```

## Output
The script will download all files which do not already exist in the target directory. For each semester a folder will be created with subfolders for each course. By default only the most recent semester will be synched. 