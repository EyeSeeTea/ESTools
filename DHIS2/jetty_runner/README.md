# jetty runner

Download the [jetty-runner.jar](https://repo1.maven.org/maven2/org/eclipse/jetty/jetty-runner/9.4.9.v20180320/jetty-runner-9.4.9.v20180320.jar),
create the configuration file `dhis.conf` file in the same directory you have the
DHIS war, and run:

```
$ bash run-dhis2-war.sh dhis.war 8080
```

This will start `dhis.war` at port 8080.
