## Setup

We need a `jetty-runner` JAR from the MVN repository. The last known working JAR is [jetty-runner-9.4.9.v20180320.jar](https://repo1.maven.org/maven2/org/eclipse/jetty/jetty-runner/9.4.9.v20180320/jetty-runner-9.4.9.v20180320.jar).

Now create a configuration file `dhis.conf` in the same directory you have the WAR. An example (replace `sierra-leone` by your DB name):

```
connection.dialect = org.hisp.dhis.hibernate.dialect.DhisPostgreSQLDialect
connection.driver_class = org.postgresql.Driver
connection.url = jdbc:postgresql:sierra-leone
#connection.url = jdbc:postgresql://localhost:5434/sierra-leone # TCP psql access
connection.username = postgres
connection.password =
connection.schema = update
system.session.timeout = 360000
```

## Usage

Start a DHIS2 at port 8034:

```
$ bash run-dhis2-war.sh dhis34.war 8034
```

## Debugging

The bash script automatically opens a debugging port at PORT-1000. So, in the previous example, the port 7034 will be accesible to debug the WAR. Proposed setup:

- Install Intellij Idea (the community edition works fine).
- Clone a dhis2-core with the exact build of the WAR you want to debug.
- Create an Idea project from the dhis2-core sources.
- Create a new debug configuration: `Run -> Debug -> Edit Configurations -> Remote -> +`.
- Attributes: `Name=dhis2:8034, Debugger model=Attach to remote JVM, Host=localhost, port=7034` -> Apply
- When the WAR is already running: `Run -> Debug -> dhis2:8034`.

Now you should see in the Debug panel: "Connected to the target VM, address: 'localhost:7034', transport: 'socket'". You are now ready to add breakpoints and stop the server wherever you want to debug.
