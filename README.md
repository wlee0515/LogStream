# LogStream
 
A simple app to monitor text file changes in a directory.


The application when active will open a chrome tab to it's web-app.

The application will monitor a folder every second and send the changes in the text files to the web-app.

The applicaiton is to be used in windows environment.

## To use:

```bash
python ApplicationDirectory\app,py -port %PORT_NUMBER" -dir %LOG_DIRECTORY%

```
### Additional arguments
-r recursive flag to go into sub folders

Additional arguments will be used as file extensions to monitor. By default .txt and .log are available 


### Example
```bash
python ApplicationDirectory\app,py -port 2000 -dir "C:\MyLogs" -r .json .xml

```