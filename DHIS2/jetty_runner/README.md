# jetty runner

Download the last version of 
[https://mvnrepository.com/artifact/org.eclipse.jetty/jetty-runner](jetty-runner.jar),
create the configuration file `dhis.conf` file in the same directory you have the
DHIS war, and run:

```
$ bash run-dhis2-war.sh dhis26.war 8081
```

This will start `dhis26.war` at port 8081.