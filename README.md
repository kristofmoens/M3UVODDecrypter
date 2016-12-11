Introduction
============

This is a tool to decrypt the m3u stream files which use AES-128 encryption. To use:

```python decryptVODStream "<url>" ```

It's important to put the quotes around the url, otherwise they will be interpreted by the shell.

This will download all the video files in the current directory and create one main file which will contain the decrypted assembled stream.