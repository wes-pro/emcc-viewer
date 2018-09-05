# emcc-viewer
#### How to use Dash framework to visualize performance data from Enterprise Manager Cloud Control

Simple demo project created for POUG 2018 Conference (Pint With Oracle User Group) (http://http://poug.org/en/edycja/poug-2018/)

## Installation on Linux

1. Create directory for installation and testing:
   ```
   mkdir <my_dir>
   ```
1. Create virtual Python 3 environment:
   ```
   cd <my_dir>
   virtualenv -p python3 python
   . python/bin/activate
   ```
1. Clone repository to peferred location:
   ```
   cd <my_dir>
   git clone https://github.com/wes-pro/emcc-viewer.git
   ```
1. Install Python libraries required by demo:
   ```
   pip install -r <my_dir>/requirements.txt
   ```
1. Install Oracle Instant Client:
   Download binaries from <br> http://www.oracle.com/technetwork/topics/linuxx86-64soft-092277.html
   
   For example you downloaded to /tmp/instantclient-basic-linux.x64-18.3.0.0.0dbru.zip
   cd <my_dir>
   unzip /tmp/instantclient-basic-linux.x64-18.3.0.0.0dbru.zip
1. Create tnsnames.ora:
   ```
   cat >instantclient_18_3/tnsnames.ora <<EOF
   OMR = 
     (DESCRIPTION =
       (ADDRESS_LIST = 
         (ADDRESS = (PROTOCOL=TCP)(HOST=<emcc_db_host>)(PORT=1521))
       )
       (LOAD_BALANCE=ON)
       (CONNECT_DATA=
         (SERVICE_NAME=<emcc_service>)
       )
     )
   EOF
   ```
1. Modify <my_dir>/emcc-viewer/config.py accordingly to your EMCC database connection and credentials
   
## Starting demo on Linux
 
1. Enable virtual Python environment
   ```
   cd <my_dir>
   . python/bin/activate
   ```
1. Set Oracle client environment
   ```
   export ORACLE_HOME=`pwd`/instantclient_18_3
   LD_LIBRARY_PATH=`pwd`/instantclient_18_3:$LD_LIBRARY_PATH
   export TNS_ADMIN=`pwd`/instantclient_18_3
   ```
1. Start demo application
   ```
   nohup python emcc-viewer/main.py &
   ```

 

